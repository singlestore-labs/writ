#include <stdlib.h>
#include <sum.h>

__attribute__((weak, export_name("canonical_abi_realloc")))
void *canonical_abi_realloc(
void *ptr,
size_t orig_size,
size_t org_align,
size_t new_size
) {
  void *ret = realloc(ptr, new_size);
  if (!ret)
  abort();
  return ret;
}

__attribute__((weak, export_name("canonical_abi_free")))
void canonical_abi_free(
void *ptr,
size_t size,
size_t align
) {
  free(ptr);
}
void sum_list_s32_free(sum_list_s32_t *ptr) {
  canonical_abi_free(ptr->ptr, ptr->len * 4, 4);
}
__attribute__((export_name("sum")))
int32_t __wasm_export_sum_sum(int32_t arg, int32_t arg0) {
  sum_list_s32_t arg1 = (sum_list_s32_t) { (int32_t*)(arg), (size_t)(arg0) };
  int32_t ret = sum_sum(&arg1);
  return ret;
}
int32_t sum_sum(sum_list_s32_t *a) {
  int32_t res = 0;
  for(int i = 0; i < a->len; ++i) {
    res += a->ptr[i];
  }
  return res;
}
