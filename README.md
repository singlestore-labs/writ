# WRIT (WASI Reactor Interface Tester)

A CLI tool that given a WIT specification, will correctly interpret and cast arguments for an arbitrarily specified function in a Wasm module, and run it.  In particular, this tool will be useful when writing and testing “reactor” style WASI modules, where there is no “main” routine to invoke.

When no WIT file is provided, the arguments will be interpreted as basic types the same way "wasmtime --invoke" works

To facilitate expression of complex types, the tool will accept JSON notation as input and produce JSON notation as output.

## Prerequisites
If you don't want to install these packages, there's an option to use Docker [below](#building-and-running-the-docker-image)
1. Download and install [Wasmtime](https://wasmtime.dev/)

2. Install [wasmtime-py](https://github.com/bytecodealliance/wasmtime-py)

3. Install [wit-bindgen](https://github.com/bytecodealliance/wit-bindgen). You might need to install [cargo](https://doc.rust-lang.org/cargo/getting-started/installation.html) first.

4. Download and install the [WASI SDK](https://github.com/WebAssembly/wasi-sdk/releases/tag/wasi-sdk-14)

## Installation
This package can be install from PyPI using pip:
```sh
pip install writ
```

## Usage
```console
$ python3 writ --help
usage: writ [-h] [-b [BINDING_PATH]] [-w [WIT_PATH]] [-v] ...

WASI Reactor Interface Tester

positional arguments:
  input_args            path to the Wasm module, function name, and arguments in JSON format

optional arguments:
  -h, --help            show this help message and exit
  -b [BINDING_PATH], --bindings [BINDING_PATH]
                        directory path to use for the binding cache
  -w [WIT_PATH], --wit [WIT_PATH]
                        path to the WIT file
  -v, --verbose         enable debug output
```

## Examples 
There are a few examples in `/data` directory. First, we `cd src` into the directory containing the source code:
1. `power` example: 
```sh
./writ --wit ../data/int/power.wit ../data/int/power.wasm power-of 2 3
./writ ../data/int/power.wasm power-of 2 3
```
Output:
```console
8
```

2. `split string` example:
```sh
./writ --wit ../data/string/split.wit ../data/string/split.wasm split-str '"wasm_rocks_the_house"' '"_"'
```
Output:
```console
[{"str": "wasm", "idx": 0}, {"str": "rocks", "idx": 5}, {"str": "the", "idx": 11}, {"str": "house", "idx": 15}]
```

3. Same `power` example, but for float type
float:
```sh
./writ --wit ../data/float/power.wit ../data/float/power.wasm power-of 2.0 3.0
```
Output:
```console
8.0
```
4. a machine learning model `sentiment analysis` example:
```
./writ --wit ../data/sentiment/sentiment.wit  ../data/sentiment/sentiment.wasm sentiment '"have a nice day"'
```
Output:
```console
{"compound": 0.4214636152117623, "positive": 0.5833333333333334, "negative": 0.0, "neutral": 0.4166666666666667}
```

5. `record` examples:
* Construct a struct `bar` giving a `string name` and an `integer age`:
```sh
./writ --wit ../data/record/record.wit ../data/record/record.wasm construct-bar '"meow"' 22
```
Output:
```console
{"name": "meow", "age": 22}
```
* Apply a function on a given struct (`bar`)
```sh
 ./writ --wit ../data/record/record.wit ../data/record/record.wasm bar '{"name": "meow", "age": 22}'
```
Output:
```console
{"name": "meow", "age": 32}
```

* Construct a nested struct given an input
```sh
./writ --wit ../data/record/record.wit ../data/record/record.wasm deeper-bar '{"name": "meow", "age": 22}'
```
Output:
```console
{"id": 2, "x": {"id": 1, "x": {"name": "meow", "age": 32}}}
```

* Apply a function on a nested struct
```sh
./writ --wit ../data/record/record.wit ../data/record/record.wasm rev-deeper-bar '{"id": 2, "x": {"id": 1, "x": {"name": "meow", "age": 32}}}'
```
Output:
```console
{"id": 4, "x": {"id": 1, "x": {"name": "meow", "age": 32}}}
```

6. Apply a function on a list of records (or any types that can be presented as JSON)
```sh
./writ --wit ../data/list_record/list_record.wit ../data/list_record/list_record.wasm test-list-record '[{"name": "doggo", "age": 42}, {"name":"meow", "age":28}]'
```
Output
```console
70
```
7. Apply a function on binary type

Notice: Bytes has to be presented as an array of integer, each integer represent one byte
```sh
./writ --wit ../data/hilbert/hilbert.wit ../data/hilbert/hilbert.wasm hilbert-encode '{"vec": [19,2,20,56,6,2,25,19], "min-value": 1.0, "max-value": 3.0, "scale": 6.0}'
```
Output:
```console
[{"idx": "0"}]
```

## Building and Running the Docker Image
You will need to install [Docker](https://docs.docker.com/engine/install/).

Set up (make sure you are at the directory containing `Dockerfile`:
```sh
docker build -t writ .
```

You can then run `writ` against the examples in this repo, as in the following
example:
```sh
docker run -it --rm -v $(pwd):/work \
    writ --wit /work/data/sentiment/sentiment.wit \
    /work/data/sentiment/sentiment.wasm \
    sentiment \
    '"have a nice day"'
```
