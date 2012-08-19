#include <stdlib.h>
int main(int argc, char *argv[]) 
{
   
   execv("/data/website-build/build/scripts/post-commit-svnup.py", argv);
   return 1;
}
