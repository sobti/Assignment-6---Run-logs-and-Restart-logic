SELECT count(*) as nr,
    Subject.name as subject,
    Term.name as term
FROM EvaluationEvent event,
    TermGrades,
    Subject,
    Term
WHERE TermGrades.subject = Subject.id
    AND TermGrades.term = Term.id
    AND TermGrades.grade in (
        WITH RECURSIVE Path(id, parent) AS (
            SELECT id,
                parent
            FROM GradeComponent
            WHERE id = event.grade
            UNION ALL
            SELECT parent.id,
                parent.parent
            FROM GradeComponent parent,
                Path child
            WHERE parent.id = child.parent
        )
        SELECT id
        FROM Path
        WHERE parent IS NULL
    )
GROUP BY Subject.id,
    Term.id
ORDER BY nr DESC, Term.startDate DESC,
    Term.name ASC,
    Subject.name ASC;