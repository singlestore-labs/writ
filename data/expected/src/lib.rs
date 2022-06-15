wit_bindgen_rust::export!("expected.wit");
struct Expected;
impl expected::Expected for Expected {
    fn power_of(base: i32, exp: i32) -> Result<i32, String> {
        if exp < 0 {
            return Err("negative exp".to_string());
        }
        let mut res = 1;
        for _i in 0..exp {
            res *= base;
        }
        Ok(res)
    }
}
