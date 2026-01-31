package main

import "C"
import (
	"encoding/json"
	"fmt"
	"sync"
	"unsafe"
)

func Search_user(C_username *C.char, C_NoFalsePositives C.char) *C.char {
	username := C.GoString(C_username)
	NoFalsePositives := C_NoFalsePositives != 0

	data, err := unmarshalJSON()
	if err != nil {
		fmt.Printf("Error unmarshalling json: %v\n", err)
		return nil
	}

	var wg sync.WaitGroup
	urlResultChan := make(chan []string, 1)

	wg.Add(1)
	go url_search(data, username, NoFalsePositives, &wg, urlResultChan)

	go func() {
		wg.Wait()
		close(urlResultChan)
	}()

	jsonData, err := json.Marshal(<-urlResultChan)
	if err != nil {
		return C.CString("[]")
	}

	// 4. Allocate on C-heap (Must be freed by Python later)
	return C.CString(string(jsonData))
}

func FreeString(ptr *C.char) {
	C.free(unsafe.Pointer(ptr))
}

func main() {}
