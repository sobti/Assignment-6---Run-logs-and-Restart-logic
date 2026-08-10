package cmd

import (
	"fmt"

	"github.com/logrusorgru/aurora"
	"github.com/spf13/cobra"
)

var tagFormatStr = fmt.Sprintf("- %s (%s)",
	aurora.Blue("%s"), aurora.Cyan("%d"))

var tagsCmd = &cobra.Command{
	Use:   "tags",
	Short: "List all tags",
	Long:  `Lists all tags used in the library.`,
	Run: func(cmd *cobra.Command, args []string) {
		// Load bookmarks from file
		bmks := ReadBookmarksFromFile()

		// Get tags
		tags := bmks.GetAllTags()

		// Print tags
		for _, tag := range tags.Tags.Tags {
			fmt.Println(fmt.Sprintf(tagFormatStr, tag, tags.Count[tag]))
		}
	},
}

func init() {
	rootCmd.AddCommand(tagsCmd)
}
