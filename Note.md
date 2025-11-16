## A personal note

```
ls *.zst | xargs -n1 -P30 -I{} zstd --rm -d {}
ls *.xz | xargs -n1 -I{} -P50 xz -d  {}
```
