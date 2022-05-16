wit_bindgen_rust::export!("record.wit");
struct Record;
use crate::record::Bar;

impl record::Record for Record {
    fn test_list_record(a: Vec<Bar>) -> i32 {
        a.iter().map(|s| s.age).sum()
    }
}
