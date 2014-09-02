typedef enum D_TYPES
{
  INT,
  LINT,
  FLOAT,
  DOUBLE,
  LDOUBLE
} DATA_TYPE;

#define SCL_IL(fun, IN, ... ) \
  int _##fun##_N_INPUTS_ = IN; \
  int _##fun##_INPUT_LEN_[IN] =  {__VA_ARGS__};

#define SCL_IT(fun, IN, ... ) \
  DATA_TYPE _##fun##_INPUT_TYPE_[IN] = {__VA_ARGS__};

#define SCL_OL(fun, ON, ...) \
  int _##fun##_N_OUTPUTS_ = ON; \
  int _##fun##_OUTPUT_LEN_[ON] = {__VA_ARGS__};

#define SCL_OT(fun, ON, ... ) \
  DATA_TYPE _##fun##_OUTPUT_TYPE_[ON] = {__VA_ARGS__};

