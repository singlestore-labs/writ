import json
import subprocess
import unittest


class TestParseJson(unittest.TestCase):
    def test_process_arg_int(self):
        pass

    def test_process_arg_float(self):
        pass

    def test_process_arg_str(self):
        pass

    def test_process_arg_bool(self):
        pass

    def test_process_arg_bytes(self):
        pass

    def test_process_arg_list(self):
        pass

    def test_process_arg_dict(self):
        pass

    def test_process_arg_mismatch(self):
        pass


def transform_to_command(wit_path: str, wasm_path: str, func: str) -> list[str]:
    return ["python3", "src/writ", "--wit", wit_path, wasm_path, func]


def run_command(command: list[str], inp: list[str]) -> str:
    result = subprocess.run(command + inp, capture_output=True)
    return result.stdout.decode("utf-8").strip()


class TestResult(unittest.TestCase):
    def test_power_int_with_arg(self):
        command = transform_to_command(
            "data/int/power.wit", "data/int/power.wasm", "power-of"
        )
        for a in range(0, 5):
            for b in range(0, 5):
                assert run_command(command, [str(a), str(b)]) == str(a ** b)

    def test_power_float(self):
        command = transform_to_command(
            "data/float/power.wit", "data/float/power.wasm", "power-of"
        )
        assert run_command(command, ["0.0", "5.0"]) == json.dumps(0.0 ** 5.0)
        assert run_command(command, ["5.0", "3.0"]) == json.dumps(5.0 ** 3.0)

    def test_sentiment(self):
        command = transform_to_command(
            "data/sentiment/sentiment.wit", "data/sentiment/sentiment.wasm", "sentiment"
        )
        assert run_command(command, ['"have a nice day"']) == json.dumps(
            {
                "compound": 0.4214636152117623,
                "positive": 0.5833333333333334,
                "negative": 0.0,
                "neutral": 0.4166666666666667,
            }
        )

    def test_split(self):
        command = transform_to_command(
            "data/string/split.wit", "data/string/split.wasm", "split-str"
        )
        assert run_command(command, ['"wasm_rocks_the_house"', '"_"']) == json.dumps(
            [
                {"str": "wasm", "idx": 0},
                {"str": "rocks", "idx": 5},
                {"str": "the", "idx": 11},
                {"str": "house", "idx": 15},
            ]
        )

    def test_construct_record(self):
        command = transform_to_command(
            "data/record/record.wit", "data/record/record.wasm", "construct-bar"
        )
        assert run_command(command, ['"meow"', str(22)]) == json.dumps(
            {"name": "meow", "age": 22}
        )

    def test_record_arg(self):
        command = transform_to_command(
            "data/record/record.wit", "data/record/record.wasm", "bar"
        )
        assert run_command(command, ['{"name": "meow", "age": 22}']) == json.dumps(
            {"name": "meow", "age": 32}
        )

    def test_construct_nested_record(self):
        command = transform_to_command(
            "data/record/record.wit", "data/record/record.wasm", "deeper-bar"
        )
        assert run_command(command, ['{"name": "meow", "age": 22}']) == json.dumps(
            {"id": 2, "x": {"id": 1, "x": {"name": "meow", "age": 32}}}
        )

    def test_nested_record_arg(self):
        command = transform_to_command(
            "data/record/record.wit", "data/record/record.wasm", "rev-deeper-bar"
        )
        assert run_command(
            command, ['{"id": 2, "x": {"id": 1, "x": {"name": "meow", "age": 32}}}']
        ) == json.dumps({"id": 4, "x": {"id": 1, "x": {"name": "meow", "age": 32}}})

    def test_list_int(self):
        command = transform_to_command(
            "data/list_int/sum.wit", "data/list_int/sum.wasm", "sum"
        )
        assert run_command(
            command, ['[1,2,3,4]']) == json.dumps(10)

    def test_list_record(self):
        command = transform_to_command(
            "data/list_record/list_record.wit", "data/list_record/list_record.wasm", "test_list_record"
        )
        assert run_command(
            command, ['[{"name": "doggo", "age": 42}, {"name":"meow", "age":28}]']) == json.dumps(70)

    def test_bytes(self):
        command = transform_to_command(
            "data/hilbert/hilbert.wit", "data/hilbert/hilbert.wasm", "hilbert-encode"
        )
        assert run_command(
            command, ['{"vec": [19,2,20,56,6,2,25,19], "min-value": 1.0, "max-value": 3.0, "scale": 6.0}']) == json.dumps([{"idx": "0"}])


if __name__ == "__main__":
    import nose2

    nose2.main()
