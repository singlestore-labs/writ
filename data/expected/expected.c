#include <stdlib.h>
#include <power.h>

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

void power_string_set(power_string_t *ret, const char *s) {
  ret->ptr = (char*) s;
  ret->len = strlen(s);
}

void power_string_dup(power_string_t *ret, const char *s) {
  ret->len = strlen(s);
  ret->ptr = canonical_abi_realloc(NULL, 0, 1, ret->len);
  memcpy(ret->ptr, s, ret->len);
}

void power_string_free(power_string_t *ret) {
  canonical_abi_free(ret->ptr, ret->len, 1);
  ret->ptr = NULL;
  ret->len = 0;
}
void power_expected_s32_string_free(power_expected_s32_string_t *ptr) {
  switch ((int32_t) ptr->tag) {
    case 1: {
      power_string_free(&ptr->val.err);
      break;
    }
  }
}

__attribute__((aligned(4)))
static uint8_t RET_AREA[12];
__attribute__((export_name("power-of")))
int32_t __wasm_export_power_power_of(int32_t arg, int32_t arg0) {
  power_expected_s32_string_t ret;
  power_power_of(arg, arg0, &ret);
  int32_t ptr = (int32_t) &RET_AREA;
  switch ((int32_t) (ret).tag) {
    case 0: {
      const int32_t *payload = &(ret).val.ok;
      *((int8_t*)(ptr + 0)) = 0;
      *((int32_t*)(ptr + 4)) = *payload;
      break;
    }
    case 1: {
      const power_string_t *payload1 = &(ret).val.err;
      *((int8_t*)(ptr + 0)) = 1;
      *((int32_t*)(ptr + 8)) = (int32_t) (*payload1).len;
      *((int32_t*)(ptr + 4)) = (int32_t) (*payload1).ptr;
      break;
    }
  }
  return ptr;
}
