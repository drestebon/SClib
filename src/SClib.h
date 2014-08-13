/* pa definir una funcion:

PYO(foo,2, 1,1);
PYO_TYPES(foo,2, FLOAT, INT)
PYI(foo,2, 1,1);
PYI_TYPES(foo,2, DOUBLE, FLOAT)
void foo(float  * of,
         int    * oi,
         double * id,
         float  * ii
         )
{
}

*/

typedef enum D_TYPES
{
  INT,
  LINT,
  FLOAT,
  DOUBLE,
  LDOUBLE
} DATA_TYPE;

#define PYI(fun, IN, ... ) \
  int _##fun##_N_INPUTS_ = IN; \
  int _##fun##_INPUT_LEN_[IN] =  {__VA_ARGS__};

#define PYI_TYPES(fun, IN, ... ) \
  DATA_TYPE _##fun##_INPUT_TYPE_[IN] = {__VA_ARGS__};

#define PYO(fun, ON, ...) \
  int _##fun##_N_OUTPUTS_ = ON; \
  int _##fun##_OUTPUT_LEN_[ON] = {__VA_ARGS__};

#define PYO_TYPES(fun, ON, ... ) \
  DATA_TYPE _##fun##_OUTPUT_TYPE_[ON] = {__VA_ARGS__};

