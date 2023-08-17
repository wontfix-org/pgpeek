# Peek into PostgreSQL query activity ಠಠ

Just a little toy project to check out `textual`, call `pgpeek <psycopg2-dsn>`

 * Table scrolling with up/down etc.
 * `i` toggles display of idle connections
 * `k` cancels the query of the selected row
 * `K` terminates the backend of the selected row
 * `c` copies the selected query to the clipboard if the terminal supports the OSC 52 control sequence

# Development

PGPEEK_DSN="<psycopg2-dsn>" textual run --dev pgpeek.application:DevApplication
