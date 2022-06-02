wit_bindgen_rust::export!("list_record.wit");
struct ListRecord;
use crate::list_record::Bar;

impl list_record::ListRecord for ListRecord {
    fn test_list_record(a: Vec<Bar>) -> i32 {
        a.iter().map(|s| s.age).sum()
    }
}
