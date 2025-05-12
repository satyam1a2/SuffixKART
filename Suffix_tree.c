#include <stdio.h>
#include<stdlib.h>
#include<string.h>
#include "Suffix_tree.h"
char *test;
SNode *root = NULL;
SNode *lastNewNode = NULL;
SNode *activeNode = NULL;
int activeEdge = -1;
int activeLength = 0;
int remainingSuffixCount = 0;
int END = -1;
int *rootEnd = NULL;
int *splitEnd = NULL;
int size = -1;
SNode *newNode(int start, int *end)
{
   SNode *STSNode = (SNode *)malloc(sizeof(SNode));
   int r = 0;
   while (r < MAX)
      STSNode->children[r++] = NULL;
   STSNode->suffixLink = root;
   STSNode->start = start;
   STSNode->end = end;
   STSNode->suffixIndex = -1;
   return STSNode;
}
int edgeLength(SNode *A)
{
   if(A==root)
      return 0;
   long int e = *(A->end);
   long int s = A->start;
   return (e - s + 1);
}
int walkDown(SNode *A)
{
   // APCFWD - Active point change for walk down using skip/count trick(Trick 1)
   if (activeLength >= edgeLength(A))
   {
      activeNode = A;
      activeLength -= edgeLength(A);
      activeEdge += edgeLength(A);
      return 1;
   }
   return 0;
}
void extendSuffixTree(int pos){
   END = pos;
   remainingSuffixCount++;
   lastNewNode = NULL;
   while(remainingSuffixCount){
      if(activeLength==0) activeEdge = pos;
      if(activeNode->children[test[activeEdge]]==NULL){
         activeNode->children[test[activeEdge]] = newNode(pos,&END);
         if(lastNewNode != NULL)
         {
            lastNewNode->suffixLink = activeNode;
            lastNewNode = NULL;
         }
      }else{
         SNode* next = activeNode->children[test[activeEdge]];
         if(walkDown(next))
         {
            continue;
         }
         if(test[next->start+activeLength]==test[pos]){
            if(lastNewNode != NULL && activeNode != root)
            {
               lastNewNode->suffixLink = activeNode;
               lastNewNode = NULL;
            }
            activeLength++;
            break;
         }
         splitEnd = (int*)malloc(sizeof(int));
         *splitEnd = next->start + activeLength - 1;
         SNode* split = newNode(next->start,splitEnd);
         activeNode->children[test[activeEdge]] = split;
         split->children[test[pos]] = newNode(pos,&END);
         next->start += activeLength;
         split->children[test[next->start]] = next;
         if(lastNewNode!=NULL){
            lastNewNode->suffixLink = split;
         }
         lastNewNode = split;
      }
      remainingSuffixCount--;
      if(activeNode==root&&activeLength>0){
         activeLength--;
         activeEdge = pos - remainingSuffixCount + 1;
      }else if(activeNode != root){
         activeNode = activeNode->suffixLink;
      }
   }
}
void print(int i, int j)
{
	int k;
	for (k=i; k<=j; k++)
		printf("%c", test[k]);
}
void setSuffixIndex(SNode *n, int labelHeight)
{
	if (n == NULL) return;
	int leaf = 1;
	int i;
	for (i = 0; i < MAX; i++)
	{
		if (n->children[i] != NULL)
		{
			leaf = 0;
			setSuffixIndex(n->children[i], labelHeight +
								edgeLength(n->children[i]));
		}
	}
	if (leaf == 1)
	{
		n->suffixIndex = size - labelHeight;
	}
}
void freeSuffixTreeByPostOrder(SNode *n)
{
    if (n == NULL)
        return;
    int i;
    for (i = 0; i < MAX; i++)
    {
        if (n->children[i] != NULL)
        {
            freeSuffixTreeByPostOrder(n->children[i]);
        }
    }
    if (n->suffixIndex == -1)
        free(n->end);
    free(n);
}
void buildSuffixTree(char * text) {
   test = text;
   size = strlen(test);
   rootEnd = (int*) malloc(sizeof(int));
   *rootEnd = -1;
   root = newNode(-1,rootEnd);
   activeNode = root;
   int j = 0;
   while(j<size)
      extendSuffixTree(j++);
   int labelHeight = 0;
   setSuffixIndex(root,labelHeight);
}
SNode* returnRoot(){
   return root;
}