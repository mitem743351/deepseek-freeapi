# Limitations

This observer cannot safely guarantee payload access for every browser transport. `NOT_OBSERVABLE` is the correct outcome when application-owned streams cannot be inspected without consuming them. SSE content type alone is not an event schema. No external JavaScript bundle is fetched or exported. IndexedDB record values are not retained; schema profiling reads at most 25 records per store and writes nothing.
