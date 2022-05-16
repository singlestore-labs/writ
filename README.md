# open-source-template
Template project for open source projects from SingleStore

## Usage

1. [Sign up](https://www.singlestore.com/try-free/) for a free SingleStore license. This allows you
   to run up to 4 nodes up to 32 gigs each for free. Grab your license key from
   [SingleStore portal](https://portal.singlestore.com/?utm_medium=osm&utm_source=github) and set it as an environment
   variable.

   ```bash
   export SINGLESTORE_LICENSE="singlestore license"
   ```

## Resources

* [Documentation](https://docs.singlestore.com)
* [Twitter](https://twitter.com/SingleStoreDevs)
* [SingleStore forums](https://www.singlestore.com/forum)

## Test 
int:
```sh
python3 ~/writ/writ.py --wit ./power.wit ./power.wasm power-of 2 3
```

string:
```sh
python3 ~/writ/writ.py --wit ./split.wit ./split.wasm split-str '"wasm_rocks_the_house"' '"_"'
```

float:
```sh
python3 ~/writ/writ.py --wit ./power.wit ./power.wasm power-of 2.5 3.4
```

record:
```sh
python3 ~/writ/writ.py --wit ./record.wit ./target/wasm32-wasi/debug/record.wasm test-record '{"name": "hi", "age": 42}'
```

list_int:
```sh
 python3 ~/writ/writ.py --wit ./sum.wit ./sum.wasm sum '[1,2,3]'
```

list_string:
```sh
python3 ~/writ/writ.py --wit ./sum.wit ./sum.wasm sum-length '["hi", "im", "a", "", "cat"]'
```

list_record:
```sh
python3 ~/writ/writ.py --wit ./record.wit ./target/wasm32-wasi/debug/record.wasm test-list-record '[{"name": "hi", "age": 42}, {"name":"meow", "age":28}]'
```
