package main

/*
#include <stdlib.h>
*/
import "C"

import (
	"AAO/search"
	"encoding/json"
	"fmt"
	"sync"
	"unsafe"
)

//export Search_user
func Search_user(C_username *C.char, C_NoFalsePositives C.char) *C.char {
	username := C.GoString(C_username)
	NoFalsePositives := C_NoFalsePositives != 0

	data, err := search.UnmarshalJSON()
	if err != nil {
		fmt.Printf("Error unmarshalling json: %v\n", err)
		return nil
	}

	var wg sync.WaitGroup
	urlResultChan := make(chan []string, 1)

	wg.Add(1)
	go search.Url_search(data, username, NoFalsePositives, &wg, urlResultChan)

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

//export FreeString
func FreeString(ptr *C.char) {
	C.free(unsafe.Pointer(ptr))
}

func main() {}
