SELECT
	COUNT(*)
FROM [MARoomTypes]
WHERE
	[TypeCd] <> @TypeCd
	AND [Slug] = @Slug