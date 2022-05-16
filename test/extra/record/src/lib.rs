wit_bindgen_rust::export!("record.wit");
struct Record;
use crate::record::Bar;
use crate::record::DeepBar;
use crate::record::DeeperBar;
use crate::record::Foo;

impl record::Record for Record {
    fn test_record(a: Bar) -> i32 {
        a.age
    }
    fn test_deep_record(a: DeepBar) -> i32 {
        a.x.age
    }
    fn test_deeper_record(a: DeeperBar) -> i32 {
        a.x.x.age
    }
    fn construct_bar(name: String, age: i32) -> Bar {
        Bar {
            name: name,
            age: age,
        }
    }
    fn bar(a: Bar) -> Bar {
        Bar {
            name: a.name,
            age: a.age + 10,
        }
    }
    fn deep_bar(a: Bar) -> DeepBar {
        DeepBar {
            id: 1,
            x: Self::bar(a),
        }
    }
    fn deeper_bar(a: Bar) -> DeeperBar {
        DeeperBar {
            id: 2,
            x: Self::deep_bar(a),
        }
    }
    fn rev_deeper_bar(a: DeeperBar) -> DeeperBar {
        DeeperBar {
            id: a.id + 2,
            x: a.x,
        }
    }
    // use for testing json output
    fn foo() -> Foo {
        Foo {
            movies: vec!["star wars 1".to_string(), "star wars 2".to_string()],
            code: vec![99, 98, 97],
            bars: vec![
                Bar {
                    name: "name1".to_string(),
                    age: 1,
                },
                Bar {
                    name: "name2".to_string(),
                    age: 2,
                },
            ],
            b: vec![true, false, true],
        }
    }
    fn test_foo(a: Foo) -> Foo {
        Foo {
            movies: a.movies.into_iter().rev().collect(),
            code: (&a.code[1..]).to_vec(),
            bars: a
                .bars
                .iter()
                .map(|_x| Bar {
                    name: "test".to_string(),
                    age: 1,
                })
                .collect::<Vec<Bar>>(),
            b: a.b,
        }
    }
}
