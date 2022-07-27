#ifndef __BINDINGS_SUM_H
#define __BINDINGS_SUM_H
#ifdef __cplusplus
extern "C"
{
  #endif

  #include <stdint.h>
  #include <stdbool.h>
  typedef struct {
    int32_t *ptr;
    size_t len;
  } sum_list_s32_t;
  void sum_list_s32_free(sum_list_s32_t *ptr);
  int32_t sum_sum(sum_list_s32_t *a);
  #ifdef __cplusplus
}
#endif
#endif
