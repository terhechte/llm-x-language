package main

import (
	"encoding/json"
	"fmt"
	"strings"
)

// WordTimestamp represents the structure of a word with timestamps
type WordTimestamp struct {
	Word string  `json:"word"`
	Start float64 `json:"start"`
	End float64   `json:"end"`
}

// ParagraphTimestamp represents the structure of the paragraph and its timestamps
type ParagraphTimestamp struct {
	Paragraph string            `json:"paragraph"`
	Timestamps []WordTimestamp  `json:"timestamps"`
}

// FindClosestWord matches the words in the source paragraph with the closest words in the timestamped list
func FindClosestWord(para ParagraphTimestamp) ([]WordTimestamp, error) {
	var result []WordTimestamp
	window := 0
	for _, ts := range para.Timestamps {
		sourceWords := strings.Split(para.Paragraph, " ")

		levDist := distance(ts.Word, sourceWords[window])

		for len(sourceWords) > window {
			if levDist == 0 {
				result = append(result, ts)
				break
			} else if window+mismatchCount(ts.Word,sourceWords[window:]) > len(sourceWords) || window+mismatchCount(ts.Word,sourceWords[window:]) < 0{
				break
			}else {
					levDist = distance(ts.Word, sourceWords[window+1])

					if sourceWords[window+1] == "" {
						break
					}
					window++
			}

		}
	}

	return result, nil
}

func matchScore(word, transcription string) int {
	score := 0
	min := 0
	for _, char := range word {
		min = 0
		for _, tchar := range transcription {
			if char == tchar {
				score++
			}
		}

		if score > min {
			min = score

		}

	}

	return min
}

func mismatchCount(currentWord string, remainingWords []string) int {
	mismatch := 0
	for _, word := range remainingWords {
		min := distance(currentWord, word)
		if min > 0 {
			mismatch += 1
		}
	}
	return mismatch
}

func distance(a, b string) int {
	la, lb := len(a), len(b)
	dp := make([][]int, 2)
	for i := 0; i < 2; i++ {
		dp[i] = make([]int, lb+1)
	}
	for i := 0; i <= lb; i++ {
		dp[0][i] = i
	}
	for i := 1; i <= la; i++ {
		dp[i%2][0] = i
		for j := 1; j <= lb; j++ {
			dp[i%2][j] = min(dp[(i-1)%2][j-1]+equal(a[i-1], b[j-1]), dp[(i-1)%2][j]+1, dp[i%2][j-1]+1)
		}
	}
	return dp[la%2][lb]
}

func equal(a, b byte) int {
	if a == b {
		return 0
	}
	return 1
}

func min(a, b, c int) int {
	if a < b && a < c {
		return a
	}
	if b < c {
		return b
	}
	return c
}

func main() {
	input := `{
		"paragraph": "I am from the U.S.",
		"timestamps": [
			{ "word": "I", "start": 0.0, "end": 1.0 },
			{ "word": "am", "start": 1.0, "end": 2.0 },
			{ "word": "from", "start": 2.0, "end": 4.0 },
			{ "word": "the", "start": 3.0, "end": 4.0 },
			{ "word": "U", "start": 4.0, "end": 4.5 },
			{ "word": "S", "start": 4.5, "end": 5.0 }
		]
	}`

	var para ParagraphTimestamp
	err := json.Unmarshal([]byte(input), &para)
	if err != nil {
		fmt.Println("Error unmarshalling JSON:", err)
		return
	}

	result, err := FindClosestWord(para)
	if err != nil {
		fmt.Println("Error finding closest word:", err)
		return
	}

	output, err := json.MarshalIndent(result, "", "  ")
	if err != nil {
		fmt.Println("Error marshalling JSON:", err)
		return
	}

	fmt.Println(string(output))
}
