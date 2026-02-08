package main

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"
	"sync"
)

func Search_user(username string, NoFalsePositives bool) []byte {

	data, err := UnmarshalJSON()
	if err != nil {
		fmt.Printf("Error unmarshalling json: %v\n", err)
		return nil
	}

	var wg sync.WaitGroup
	urlResultChan := make(chan []string, 1)

	wg.Add(1)
	go Url_search(data, username, NoFalsePositives, &wg, urlResultChan)

	go func() {
		wg.Wait()
		close(urlResultChan)
	}()

	jsonData, err := json.Marshal(<-urlResultChan)
	if err != nil {
		return nil
	}

	return jsonData
}

func main() {
	http.HandleFunc("GET /search-user", func(w http.ResponseWriter, r *http.Request) {
		q := r.URL.Query()
		username := q.Get("username")
		NoFalsePositives_str := q.Get("noFalsePositives")

		NoFalsePositives, err := strconv.ParseBool(NoFalsePositives_str)
		if err != nil {
			http.Error(w, "Cant parse noFalsePositives", http.StatusBadRequest)
			return
		}

		result := Search_user(username, NoFalsePositives)

		w.Header().Set("Content-Type", "application/json")
		w.Write(result)
	})

	http.HandleFunc("GET /", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("hi"))
	})

	http.ListenAndServe(":8000", nil)
}
