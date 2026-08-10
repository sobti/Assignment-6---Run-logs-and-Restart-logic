package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"time"
)

// JSON Writes the interface to the wire
func JSON(writer http.ResponseWriter, v interface{}) {
	if body, err := json.Marshal(v); err != nil {
		ServerError(writer, err)
	} else {
		writer.Write(body)
	}
}

// JSONB Just the bytes mam
func JSONB(v interface{}) []byte {
	b, _ := json.Marshal(v)
	return b
}

// NotFoundError Writer 404 {error: not fount}
func NotFoundError(writer http.ResponseWriter, kind string, key int64, err error) {
	log.Printf("Error finding %s:%d %s\n", kind, key, err)
	writer.WriteHeader(http.StatusNotFound)
	writer.Write(JSONB(map[string]error{"error": err}))
}

func BadRequest(writer http.ResponseWriter, err error) {
	log.Println("Bad request:", err)
	writer.WriteHeader(400)
	writer.Write(JSONB(map[string]error{"error": err}))
}

func ServerError(writer http.ResponseWriter, err error) {
	fmt.Println("Error:", err)
	writer.WriteHeader(500)
}

func Unauthorized(writer http.ResponseWriter, v interface{}) {
	writer.WriteHeader(http.StatusUnauthorized)
}

func ParseTime(timeString string) time.Time {
	t, err := time.Parse(time.RFC3339, timeString)
	if err != nil {
		log.Println("Error parsing time:", err)
	}
	return t
}
