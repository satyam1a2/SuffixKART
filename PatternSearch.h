#ifndef PATTERN_SEARCH_H
#include"Suffix_tree.h"
#define PATTERN_SEARCH_H
#define MAX 256
int traverseEdge(char *str, int idx, int start, int end,char* text);
int doTraversalToCountLeaf(SNode *n);
int countLeaf(SNode *n);
int doTraversal(SNode *n, char* str, int idx,char* text);
void checkForSubString(char* str,SNode* root,char* text,int* pos);
#endif
