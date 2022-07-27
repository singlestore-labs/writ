#ifndef __BINDINGS_POWER_H
#define __BINDINGS_POWER_H
#ifdef __cplusplus
extern "C"
{
  #endif

  #include <stdint.h>
  #include <stdbool.h>

  typedef struct {
    char *ptr;
    size_t len;
  } power_string_t;

  void power_string_set(power_string_t *ret, const char *s);
  void power_string_dup(power_string_t *ret, const char *s);
  void power_string_free(power_string_t *ret);
  typedef struct {
    // 0 if `val` is `ok`, 1 otherwise
    uint8_t tag;
    union {
      int32_t ok;
      power_string_t err;
    } val;
  } power_expected_s32_string_t;
  void power_expected_s32_string_free(power_expected_s32_string_t *ptr);
  void power_power_of(int32_t base, int32_t exp, power_expected_s32_string_t *ret0);
  #ifdef __cplusplus
}
#endif
#endif
