#include <stdio.h>
#include <stdlib.h>
#include "char_operations.h"

int main()
{
    char(**funcs)(char);
    funcs = malloc(4 * sizeof(char (*)(char)));
    if(funcs == NULL)
    {
        printf("Failed to allocate memory\n");
        return 8;
    }

    *(funcs + 0) = lower_to_upper;
    *(funcs + 1) = upper_to_lower;
    *(funcs + 2) = space_to_dash;
    *(funcs + 3) = reverse_letter;

    int option;
    char *text = malloc(1001 * sizeof(char));
    if (text == NULL)
    {
        printf("Failed to allocate memory\n");
        free(funcs);
        return 8;
    }

    printf("Podaj text: ");
    scanf("%1000[^\n]s", text);

    //Clear buff
    while(getchar()!='\n'){}

    printf("Podaj opcje do wyknania: ");
    if (scanf("%d", &option) != 1)
    {
        printf("Incorrect input\n");
        free(text);
        free(funcs);
        return 1;
    }
    if (option < 0 || option > 3)
    {
        printf("Incorrect input data\n");
        free(text);
        free(funcs);
        return 2;
    }

    char *newText;

    switch (option)
    {
        case 0:
            newText = letter_modifier(text, lower_to_upper);
            break;
        case 1:
            newText = letter_modifier(text, upper_to_lower);
            break;
        case 2:
            newText = letter_modifier(text, space_to_dash);
            break;
        case 3:
            newText = letter_modifier(text, reverse_letter);
            break;
        default:
            break;
    }

    if (newText == NULL)
    {
        printf("Failed to allocate memory\n");
        free(text);
        free(funcs);
        return 8;
    }

    printf("%s", newText);


    free(text);
    free(newText);
    free(funcs);
    return 0;
}
