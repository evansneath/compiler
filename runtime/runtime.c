#include "runtime.h"

//////////////////////////////////////////////////////////////////////////////
// String functions
//

void getString(char* my_string) {
    scanf("%s", my_string);
}

void putString(char* my_string) {
    printf("%s", my_string);
}

//////////////////////////////////////////////////////////////////////////////
// Bool functions
//

int getBool() {
    int my_bool;
    scanf("%d", &my_bool);
    return my_bool ? 1 : 0;
}

void putBool(int my_bool) {
    printf("%s", my_bool ? "true" : "false");
}

//////////////////////////////////////////////////////////////////////////////
// Integer functions
//

int getInteger() {
    int my_integer;
    scanf("%d", &my_integer);
    return my_integer;
}

void putInteger(int my_integer) {
    printf("%d", my_integer);
}

//////////////////////////////////////////////////////////////////////////////
// Float functions
//

float getFloat() {
    float my_float;
    scanf("%f", &my_float);
    return my_float;
}

void putFloat(float my_float) {
    printf("%f", my_float);
}
