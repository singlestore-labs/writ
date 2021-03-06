#include <stdlib.h>
#include <power.h>
#include <math.h>

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
__attribute__((export_name("power-of")))
float __wasm_export_power_power_of(float arg, float arg0) {
  float ret = power_power_of(arg, arg0);
  return ret;
}
float power_power_of(float base, float exp)
{
    return powf(base, exp);
}
