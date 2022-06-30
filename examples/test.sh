#!/bin/bash
test_path="/home/$USER/memsql/lockfreetest/wasm_data"
wasm_path="$test_path/modules"
wit_path="$test_path/specs"
writ="python3 $(cd $(dirname $0) && pwd)/../src/writ"

function run_mult {
  local a=2
  local b=3
  echo "running mult test with arguments $a $b"
  $writ $wasm_path/mult.wasm mult $a $b
  $writ --wit $wit_path/mult.wit $test_path/modules/mult.wasm mult 2 3
  echo ""
}

function run_hilbert {
  local vec=[19,2,20,56,6,2,25,19]
  local min_value=1.0
  local max_value=3.0
  local scale=6.0
  local input="{\"vec\":$vec,\"min_value\":$min_value,\"max_value\":$max_value,\"scale\":$scale}"
  echo "running hilbert test with arguments: $input"
  # $writ $wasm_path/hilbert.wasm hilbert_encode $input
  # echo ""
  $writ --wit $wit_path/hilbert.wit $test_path/modules/hilbert.wasm hilbert-encode $input
  echo ""
}

function run_align {
  local a=1
  local b=2
  local c=3
  local d=4
  local e=5
  local f=6
  local g=7
  local h=8
  local i=9
  local j=10
  local k=11
  local l=12
  local m=13

  local input="{\"a\":$a,\"b\":$b,\"c\":$c,\"d\":$d,\"e\":\"$e\",\"f\":$f,\"g\":$g,\"h\":$h,\"i\":$i,\"j\":$j,\"k\":$k,\"l\":$l,\"m\":$m}"
  echo "running align test, function numbers-record-args with arguments $input:"
  $writ --wit $wit_path/align.wit $test_path/modules/align.wasm numbers-record-args $input
  echo ""
  echo "running align test, function make-numbers-record with arguments:"
  $writ --wit $wit_path/align.wit $test_path/modules/align.wasm make-numbers-record
  echo ""
  echo "running align test, function make-numbers-array with arguments:"
  $writ --wit $wit_path/align.wit $test_path/modules/align.wasm make-numbers-array
  echo ""
  echo "running align test, function numbers-record-rets with arguments:"
  $writ --wit $wit_path/align.wit $test_path/modules/align.wasm numbers-record-rets
  echo ""
  echo "running align test, function numbers-array-rets with arguments:"
  $writ --wit $wit_path/align.wit $test_path/modules/align.wasm numbers-array-rets
  echo ""
}

function run_alloc {
  local size=100000  
  echo "running alloc test, function alloc-blob with arguments: $size"
  $writ --wit $wit_path/alloc.wit $test_path/modules/alloc.wasm alloc-blob $size
  echo ""
}

function run_createthread {
  echo "running createthread test, function create-thread with arguments: "
  $writ --wit $wit_path/createthread.wit $test_path/modules/createthread.wasm create-thread 
  echo ""
}

function run_deeparg {
  local name="name"
  local num=0.0
  local deepestinput="{\"name\":\"$name\",\"id\":0,\"num\":$num}"

  local rec1name="rec1_name"
  local num1=1.0
  local rec1="{\"name\":\"$rec1name\",\"id\":1,\"num\":$num1}"

  local rec2name="rec2_name"
  local num2=2.0
  local rec2="{\"name\":\"$rec2name\",\"id\":2,\"num\":$num2}"

  local dname="deepername"
  local deeperinput="{\"id\":3,\"rec1\":$rec1,\"arr\":[$deepestinput, $rec1], \"name\":\"$dname\", \"rec2\":$rec2}"

  local dname1="deepername1"
  local deeperinput1="{\"id\":4,\"rec1\":$rec1,\"arr\":[$deepestinput, $rec2], \"name\":\"$dname1\", \"rec2\":$rec2}"

  local dname2="deepername2"
  local deeperinput2="{\"id\":5,\"rec1\":$rec1,\"arr\":[$rec1, $rec2], \"name\":\"$dname2\", \"rec2\":$rec2}"

  local ddname="deepname"
  local arr="[$deeperinput1, $deeperinput2]"
  local rec=$deeperinput
  local deepinput="{\"name\":\"$ddname\",\"arr\":$arr,\"rec\":$rec}"

  printf "running deeparg test, function deeparg with arguments: $deepinput \n $deeperinput \n $deepestinput"
  $writ --wit $wit_path/deeparg.wit $test_path/modules/deeparg.wasm deeparg "$deepinput" "$deeperinput" "$deepestinput"
  echo ""
}

function run_filter_users {
  local arg1=1
  local arg2="meow"
  local email="meow@cat.com"
  local phone="99999999"
  local user="{\"arg1\":$arg1,\"arg2\":\"$arg2\",\"email\":\"$email\",\"phone\":\"$phone\"}"

  echo "running filter_users test, function filter-out-bad-users with arguments: $user"
  $writ --wit $wit_path/filter_users.wit $test_path/modules/filter_users.wasm filter-out-bad-users $user
  echo ""
}

function run_passthru {
  local input1="\"hi1\""
  local input2="\"hi2\""

  echo "running passthru test, function passthrutwo with arguments: $input1 $input2"
  $writ --wit $wit_path/passthru.wit $test_path/modules/passthru.wasm passthrutwo $input1 $input2
  echo ""
}

function run_prime {
  local a=2
  local b=10
  echo "running prime test with arguments $a "
  $writ $wasm_path/prime.wasm is-prime $a 
  echo "running prime test with arguments $b "
  $writ --wit $wit_path/prime.wit $test_path/modules/prime.wasm is-prime $b
  echo ""
}

function run_plus {
  local a=2
  local b=10
  echo "running plus test with arguments $a $b"
  $writ $wasm_path/plus.wasm plus $a $b 
  echo ""
}

function run_types-basicabi {
  local i32=99
  local i64=99999999999
  local f32=3.14
  local f64=999999999.9999999
  echo "running test_i32 test with arguments: $i32"
  $writ $wasm_path/types-basicabi.wasm test_i32 $i32
  echo "running test_i64 test with arguments: $i64"
  $writ $wasm_path/types-basicabi.wasm test_i64 $i64
  echo "running test_f32 test with arguments: $f32"
  $writ $wasm_path/types-basicabi.wasm test_f32 $f32
  echo "running test_f64 test with arguments: $f64"
  $writ $wasm_path/types-basicabi.wasm test_f64 $f64
  echo "running test_noarg test with arguments: "
  $writ $wasm_path/types-basicabi.wasm test_noarg 
  echo "running test_noret test with arguments: "
  $writ $wasm_path/types-basicabi.wasm test_noret 
  echo "running test_noargnoret test with arguments: "
  $writ $wasm_path/types-basicabi.wasm test_noargnoret
}

function run_infinite {
  echo "running infinite test with arguments: "
  $writ $wasm_path/infinite.wasm opt-infinite
  echo ""
}


function run_tests {
#  run_mult
#  run_align
#  run_alloc
  run_deeparg 
#  run_hilbert
#  run_filter_users
#  run_passthru
#  run_prime
#  run_plus 
#  run_types-basicabi
#  run_infinite 
}

run_tests
