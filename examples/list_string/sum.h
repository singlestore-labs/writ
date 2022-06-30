#ifndef __BINDINGS_SUM_H
#define __BINDINGS_SUM_H
#ifdef __cplusplus
extern "C"
{
  #endif
  
  #include <stdint.h>
  #include <stdbool.h>
  
  typedef struct {
    char *ptr;
    size_t len;
  } sum_string_t;
  
  void sum_string_set(sum_string_t *ret, const char *s);
  void sum_string_dup(sum_string_t *ret, const char *s);
  void sum_string_free(sum_string_t *ret);
  typedef struct {
    sum_string_t *ptr;
    size_t len;
  } sum_list_string_t;
  void sum_list_string_free(sum_list_string_t *ptr);
  int32_t sum_sum_length(sum_list_string_t *a);
  #ifdef __cplusplus
}
#endif
#endif
