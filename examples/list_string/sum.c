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
#include <string.h>

void sum_string_set(sum_string_t *ret, const char *s) {
  ret->ptr = (char*) s;
  ret->len = strlen(s);
}

void sum_string_dup(sum_string_t *ret, const char *s) {
  ret->len = strlen(s);
  ret->ptr = canonical_abi_realloc(NULL, 0, 1, ret->len);
  memcpy(ret->ptr, s, ret->len);
}

void sum_string_free(sum_string_t *ret) {
  canonical_abi_free(ret->ptr, ret->len, 1);
  ret->ptr = NULL;
  ret->len = 0;
}
void sum_list_string_free(sum_list_string_t *ptr) {
  for (size_t i = 0; i < ptr->len; i++) {
    sum_string_free(&ptr->ptr[i]);
  }
  canonical_abi_free(ptr->ptr, ptr->len * 8, 4);
}
__attribute__((export_name("sum-length")))
int32_t __wasm_export_sum_sum_length(int32_t arg, int32_t arg0) {
  sum_list_string_t arg1 = (sum_list_string_t) { (sum_string_t*)(arg), (size_t)(arg0) };
  int32_t ret = sum_sum_length(&arg1);
  return ret;
}
int32_t sum_sum_length(sum_list_string_t *a) {
  int32_t res = 0;
  for(int i = 0; i < a->len; ++i) {
    res += a->ptr[i].len;
  }
  return res;
}
