package main

import (
	"compress/gzip"
	"compress/zlib"
	"crypto/tls"
	"fmt"
	"io"
	"net"
	"net/http"
	"os"
	"strings"
	"sync"
	"sync/atomic"
	"time"

	"github.com/andybalholm/brotli"
	"github.com/bytedance/sonic"
)

var (

	// tlsConfig defines the TLS configuration for secure HTTP requests.
	tlsConfig = &tls.Config{
		MinVersion: tls.VersionTLS12, // Minimum TLS version
		CipherSuites: []uint16{ // Supported cipher suites
			tls.TLS_AES_128_GCM_SHA256,
			tls.TLS_AES_256_GCM_SHA384,
			tls.TLS_CHACHA20_POLY1305_SHA256,
			tls.TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256,
			tls.TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256,
			tls.TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384,
			tls.TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384,
			tls.TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305_SHA256,
			tls.TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305_SHA256,
		},
		CurvePreferences: []tls.CurveID{tls.X25519, tls.CurveP256, tls.CurveP384}, // Preferred elliptic curves
		NextProtos:       []string{"http/1.1"},                                    // Supported protocols
	}

	// count tracks the number of found profiles using atomic operations for thread safety.
	count atomic.Uint32

	// file mutext
	mu sync.Mutex
)

// Cookie represents an HTTP cookie.
type cookie struct {
	Name  string `json:"name"`  // Cookie name
	Value string `json:"value"` // Cookie value
}

// Website represents a website configuration for searching usernames.
type website struct {
	Name            string   `json:"name"`                   // Website name
	BaseURL         string   `json:"base_url"`               // Base URL template
	URLProbe        string   `json:"url_probe,omitempty"`    // Optional probe URL
	FollowRedirects bool     `json:"follow_redirects"`       // Whether to follow HTTP redirects
	UserAgent       string   `json:"user_agent,omitempty"`   // Custom User-Agent, if any
	ErrorType       string   `json:"errorType"`              // Type of error checking
	ErrorMsg        string   `json:"errorMsg,omitempty"`     // Expected error message for non-existent profiles
	ErrorCode       int      `json:"errorCode,omitempty"`    // Expected HTTP status code for non-existent profiles
	ResponseURL     string   `json:"response_url,omitempty"` // Expected response URL for existing profiles
	Cookies         []cookie `json:"cookies,omitempty"`      // Cookies to include in requests
}

// Data holds the list of websites to search.
type data struct {
	Websites []website `json:"websites"` // List of website configurations
}

// User-Agent header used in HTTP requests to mimic a browser.
const DefaultUserAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0"

// UnmarshalJSON fetches and parses the website configuration from a remote JSON file.
func UnmarshalJSON() (data, error) {
	// GoSearch relies on data.json to determine the websites to search for.
	// Instead of forcing users to manually download the data.json file, we will fetch the latest version from the repository.
	// Therefore, we will do the following:
	// 1. Delete the existing data.json file if it exists as it will be outdated in the future
	// 2. Read the latest data.json file from the repository
	// Bonus: it does not download the data.json file, it just reads it from the repository.

	// Delete existing data.json file
	err := os.Remove("data.json")
	if err != nil && !os.IsNotExist(err) {
		return data{}, fmt.Errorf("error deleting old data.json: %w", err)
	}

	// Fetch JSON from repository
	url := "https://raw.githubusercontent.com/ibnaleem/gosearch/refs/heads/main/data.json"
	resp, err := http.Get(url)
	if err != nil {
		return data{}, fmt.Errorf("error downloading data.json: %w", err)
	}
	defer resp.Body.Close()

	// Check HTTP status
	if resp.StatusCode != http.StatusOK {
		return data{}, fmt.Errorf("failed to download data.json, status code: %d", resp.StatusCode)
	}

	// Read response body
	jsonData, err := io.ReadAll(resp.Body)
	if err != nil {
		return data{}, fmt.Errorf("error reading downloaded content: %w", err)
	}

	// Unmarshal JSON into Data struct
	var data_ data
	err = sonic.Unmarshal(jsonData, &data_)
	if err != nil {
		return data{}, fmt.Errorf("error unmarshalling JSON: %w", err)
	}

	return data_, nil
}

func buildURL(baseURL, username string) string {
	return strings.Replace(baseURL, "{}", username, 1)
}

// MakeRequestWithResponseURL checks for profile existence by comparing the response URL.
func makeRequestWithResponseURL(website website, url string, username string) string {
	// Some websites always return a 200 for existing and non-existing profiles.
	// If we do not follow redirects, we could get a 301 for existing profiles and 302 for non-existing profiles.
	// That is why we have the follow_redirects in our website struct.
	// However, sometimes the website returns 301 for existing profiles and non-existing profiles.
	// This means even if we do not follow redirects, we still get false positives.
	// To mitigate this, we can examine the response url to check for non-existing profiles.
	// Usually, a response url pointing to where the profile should be is returned for existing profiles.
	// If the response url is not pointing to where the profile should be, then the profile does not exist.

	// Initialize HTTP client with timeout and transport settings
	client := &http.Client{
		Timeout: 120 * time.Second,
		Transport: &http.Transport{
			TLSClientConfig: tlsConfig,
			Proxy:           http.ProxyFromEnvironment,
			DialContext: (&net.Dialer{
				Timeout:   30 * time.Second,
				KeepAlive: 30 * time.Second,
				DualStack: true,
			}).DialContext,
			MaxIdleConns:          100,
			IdleConnTimeout:       90 * time.Second,
			TLSHandshakeTimeout:   10 * time.Second,
			ExpectContinueTimeout: 1 * time.Second,
		},
		Jar: nil,
	}

	// Disable redirects if specified
	if !website.FollowRedirects {
		client.CheckRedirect = func(req *http.Request, via []*http.Request) error {
			return http.ErrUseLastResponse
		}
	}

	// Set User-Agent
	userAgent := DefaultUserAgent
	if website.UserAgent != "" {
		userAgent = website.UserAgent
	}

	// Create request
	req, err := http.NewRequest(http.MethodGet, url, nil)
	if err != nil {
		fmt.Printf("Error creating request in function MakeRequestWithResponseURL: %v\n", err)
		return ""
	}

	// Set request headers
	req.Header.Set("User-Agent", userAgent)
	req.Header.Set("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8")
	req.Header.Set("Accept-Language", "en-US,en;q=0.5")
	req.Header.Set("Accept-Encoding", "gzip, deflate, br")
	req.Header.Set("Connection", "keep-alive")
	req.Header.Set("Upgrade-Insecure-Requests", "1")
	req.Header.Set("Sec-Fetch-Dest", "document")
	req.Header.Set("Sec-Fetch-Mode", "navigate")
	req.Header.Set("Sec-Fetch-Site", "none")
	req.Header.Set("Sec-Fetch-User", "?1")
	req.Header.Set("Cache-Control", "max-age=0")

	// Add cookies if specified
	if website.Cookies != nil {
		for _, cookie := range website.Cookies {
			cookieObj := &http.Cookie{
				Name:  cookie.Name,
				Value: cookie.Value,
			}
			req.AddCookie(cookieObj)
		}
	}

	// Send request
	res, err := client.Do(req)
	if err != nil {
		return ""
	}
	defer res.Body.Close()

	// Check for error status codes
	if res.StatusCode >= 400 {
		return ""
	}

	// Compare response URL with expected URL
	formattedResponseURL := buildURL(website.ResponseURL, username)
	if !(res.Request.URL.String() == formattedResponseURL) {
		url = buildURL(website.BaseURL, username)
		count.Add(1)

		return url
	}

	return ""
}

// MakeRequestWithErrorCode checks for profile existence by comparing HTTP status codes.
func makeRequestWithErrorCode(website website, url string, username string) string {
	// Initialize HTTP client
	client := &http.Client{
		Timeout: 120 * time.Second,
		Transport: &http.Transport{
			TLSClientConfig: tlsConfig,
			Proxy:           http.ProxyFromEnvironment,
			DialContext: (&net.Dialer{
				Timeout:   30 * time.Second,
				KeepAlive: 30 * time.Second,
				DualStack: true,
			}).DialContext,
			MaxIdleConns:          100,
			IdleConnTimeout:       90 * time.Second,
			TLSHandshakeTimeout:   10 * time.Second,
			ExpectContinueTimeout: 1 * time.Second,
		},
		Jar: nil,
	}

	// Disable redirects if specified
	if !website.FollowRedirects {
		client.CheckRedirect = func(req *http.Request, via []*http.Request) error {
			return http.ErrUseLastResponse
		}
	}

	// Set User-Agent
	userAgent := DefaultUserAgent
	if website.UserAgent != "" {
		userAgent = website.UserAgent
	}

	// Create request
	req, err := http.NewRequest(http.MethodGet, url, nil)
	if err != nil {
		fmt.Printf("Error creating request in function MakeRequestWithErrorCode: %v\n", err)
		return ""
	}

	// Set request headers
	req.Header.Set("User-Agent", userAgent)
	req.Header.Set("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8")
	req.Header.Set("Accept-Language", "en-US,en;q=0.5")
	req.Header.Set("Accept-Encoding", "gzip, deflate, br")
	req.Header.Set("Connection", "keep-alive")
	req.Header.Set("Upgrade-Insecure-Requests", "1")
	req.Header.Set("Sec-Fetch-Dest", "document")
	req.Header.Set("Sec-Fetch-Mode", "navigate")
	req.Header.Set("Sec-Fetch-Site", "none")
	req.Header.Set("Sec-Fetch-User", "?1")
	req.Header.Set("Cache-Control", "max-age=0")

	// Add cookies if specified
	if website.Cookies != nil {
		for _, cookie := range website.Cookies {
			cookieObj := &http.Cookie{
				Name:  cookie.Name,
				Value: cookie.Value,
			}
			req.AddCookie(cookieObj)
		}
	}

	// Send request
	res, err := client.Do(req)
	if err != nil {
		return ""
	}
	defer res.Body.Close()

	// Check for error status codes
	if res.StatusCode >= 400 {
		return ""
	}

	// Check if status code differs from error code
	if res.StatusCode != website.ErrorCode {
		url = buildURL(website.BaseURL, username)
		count.Add(1)

		return url
	}

	return ""
}

// MakeRequestWithErrorMsg checks for profile existence by searching for an error message in the response body.
func makeRequestWithErrorMsg(website website, url string, username string) string {
	// Initialize HTTP client
	client := &http.Client{
		Timeout: 120 * time.Second,
		Transport: &http.Transport{
			TLSClientConfig: tlsConfig,
			Proxy:           http.ProxyFromEnvironment,
			DialContext: (&net.Dialer{
				Timeout:   30 * time.Second,
				KeepAlive: 30 * time.Second,
				DualStack: true,
			}).DialContext,
			MaxIdleConns:          100,
			IdleConnTimeout:       90 * time.Second,
			TLSHandshakeTimeout:   10 * time.Second,
			ExpectContinueTimeout: 1 * time.Second,
		},
		Jar: nil,
	}

	// Disable redirects if specified
	if !website.FollowRedirects {
		client.CheckRedirect = func(req *http.Request, via []*http.Request) error {
			return http.ErrUseLastResponse
		}
	}

	// Set User-Agent
	userAgent := DefaultUserAgent
	if website.UserAgent != "" {
		userAgent = website.UserAgent
	}

	// Create request
	req, err := http.NewRequest(http.MethodGet, url, nil)
	if err != nil {
		fmt.Printf("Error creating request in function MakeRequestWithErrorMsg: %v\n", err)
		return ""
	}

	// Set request headers
	req.Header.Set("User-Agent", userAgent)
	req.Header.Set("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8")
	req.Header.Set("Accept-Language", "en-US,en;q=0.5")
	req.Header.Set("Accept-Encoding", "gzip, deflate, br")
	req.Header.Set("Connection", "keep-alive")
	req.Header.Set("Upgrade-Insecure-Requests", "1")
	req.Header.Set("Sec-Fetch-Dest", "document")
	req.Header.Set("Sec-Fetch-Mode", "navigate")
	req.Header.Set("Sec-Fetch-Site", "none")
	req.Header.Set("Sec-Fetch-User", "?1")
	req.Header.Set("Cache-Control", "max-age=0")

	// Add cookies if specified
	if website.Cookies != nil {
		for _, cookie := range website.Cookies {
			cookieObj := &http.Cookie{
				Name:  cookie.Name,
				Value: cookie.Value,
			}
			req.AddCookie(cookieObj)
		}
	}

	// Send request
	res, err := client.Do(req)
	if err != nil {
		return ""
	}
	// Handle response body compression
	var reader io.ReadCloser
	switch res.Header.Get("Content-Encoding") {
	case "gzip":
		gzReader, err := gzip.NewReader(res.Body)
		if err != nil {
			fmt.Printf("Error creating gzip reader: %v\n", err)
			return ""
		}
		reader = gzReader
	case "deflate":
		zlibReader, err := zlib.NewReader(res.Body)
		if err != nil {
			fmt.Printf("Error creating deflate reader: %v\n", err)
			return ""
		}
		reader = zlibReader
	case "br":
		reader = io.NopCloser(brotli.NewReader(res.Body))
	default:
		reader = res.Body
	}
	defer res.Body.Close()

	// Check for error status codes
	if res.StatusCode >= 400 {
		return ""
	}

	// Read response body
	body, err := io.ReadAll(reader)
	if err != nil {
		fmt.Printf("Error reading response body: %v\n", err)
		return ""
	}

	// Check for error message
	bodyStr := string(body)
	if !strings.Contains(bodyStr, website.ErrorMsg) {
		url = buildURL(website.BaseURL, username)
		count.Add(1)

		return url
	}

	return ""
}

// MakeRequestWithProfilePresence checks for profile existence by searching for a profile indicator in the response body.
func makeRequestWithProfilePresence(website website, url string) string {
	// Some websites have an indicator that a profile exists
	// but do not have an indicator when a profile does not exist.
	// If a profile indicator is not found, we can assume that the profile does not exist.

	// Initialize HTTP client
	client := &http.Client{
		Timeout: 120 * time.Second,
		Transport: &http.Transport{
			TLSClientConfig: tlsConfig,
			Proxy:           http.ProxyFromEnvironment,
			DialContext: (&net.Dialer{
				Timeout:   30 * time.Second,
				KeepAlive: 30 * time.Second,
				DualStack: true,
			}).DialContext,
			MaxIdleConns:          100,
			IdleConnTimeout:       90 * time.Second,
			TLSHandshakeTimeout:   10 * time.Second,
			ExpectContinueTimeout: 1 * time.Second,
		},
		Jar: nil,
	}

	// Disable redirects if specified
	if !website.FollowRedirects {
		client.CheckRedirect = func(req *http.Request, via []*http.Request) error {
			return http.ErrUseLastResponse
		}
	}

	// Set User-Agent
	userAgent := DefaultUserAgent
	if website.UserAgent != "" {
		userAgent = website.UserAgent
	}

	// Create request
	req, err := http.NewRequest(http.MethodGet, url, nil)
	if err != nil {
		fmt.Printf("Error creating request in function MakeRequestWithErrorMsg: %v\n", err)
		return ""
	}

	// Set request headers
	req.Header.Set("User-Agent", userAgent)
	req.Header.Set("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8")
	req.Header.Set("Accept-Language", "en-US,en;q=0.5")
	req.Header.Set("Accept-Encoding", "gzip, deflate, br")
	req.Header.Set("Connection", "keep-alive")
	req.Header.Set("Upgrade-Insecure-Requests", "1")
	req.Header.Set("Sec-Fetch-Dest", "document")
	req.Header.Set("Sec-Fetch-Mode", "navigate")
	req.Header.Set("Sec-Fetch-Site", "none")
	req.Header.Set("Sec-Fetch-User", "?1")
	req.Header.Set("Cache-Control", "max-age=0")

	// Add cookies if specified
	if website.Cookies != nil {
		for _, cookie := range website.Cookies {
			cookieObj := &http.Cookie{
				Name:  cookie.Name,
				Value: cookie.Value,
			}
			req.AddCookie(cookieObj)
		}
	}

	// Send request
	res, err := client.Do(req)
	if err != nil {
		return ""
	}
	defer res.Body.Close()

	// Check for error status codes
	if res.StatusCode >= 400 {
		return ""
	}

	// Read response body
	body, err := io.ReadAll(res.Body)
	if err != nil {
		fmt.Printf("Error reading response body: %v\n", err)
		return ""
	}

	// Check for profile indicator
	bodyStr := string(body)
	if strings.Contains(bodyStr, website.ErrorMsg) {
		count.Add(1)

		return url
	}

	return ""
}

// Search performs concurrent searches across all configured websites.
func Url_search(data_ data, username string, noFalsePositives bool, wg *sync.WaitGroup, resultChan chan []string) {
	defer wg.Done()

	var url_results []string
	var internalWg sync.WaitGroup
	var mu sync.Mutex

	// Iterate over websites
	internalWg.Add(len(data_.Websites))
	for _, website_ := range data_.Websites {
		// Run search in a goroutine
		go func(website_ website) {
			defer internalWg.Done()
			var url string
			var urlO string

			// Use probe URL if specified, otherwise use base URL
			if website_.URLProbe != "" {
				url = buildURL(website_.URLProbe, username)
			} else {
				url = buildURL(website_.BaseURL, username)
			}

			// Handle different error types
			switch website_.ErrorType {
			case "status_code":
				urlO = makeRequestWithErrorCode(website_, url, username)
			case "errorMsg":
				urlO = makeRequestWithErrorMsg(website_, url, username)
			case "profilePresence":
				urlO = makeRequestWithProfilePresence(website_, url)
			case "response_url":
				urlO = makeRequestWithResponseURL(website_, url, username)
			default:
				// Handle unverified profiles if false positives are allowed
				if !noFalsePositives {
					urlO = url
				} else {
					urlO = ""
				}
			}

			if urlO != "" {
				mu.Lock()
				url_results = append(url_results, urlO)
				mu.Unlock()
			}
		}(website_)
	}

	// wait internal goroutine to finish
	internalWg.Wait()
	resultChan <- url_results
}
