#include"Suffix_tree.h"
#include"PatternSearch.h"
#include<stdio.h>
int* test2;
int ind = 0;
int traverseEdge(char *str, int idx, int start, int end,char* text)
{
    int k = 0;
    for(k=start; k<=end && str[idx] != '\0'; k++, idx++)
    {
        if(text[k] != str[idx])
            return -1; 
    }
    if(str[idx] == '\0')
        return 1;
    return 0;  
}
int doTraversalToCountLeaf(SNode *n)
{
    if(n == NULL)
        return 0;
    if(n->suffixIndex > -1)
    {
        test2[ind++] = n->suffixIndex;
        return 1;
    }
    int count = 0;
    int i = 0;
    for (i = 0; i < MAX; i++)
    {
        if(n->children[i] != NULL)
        {
            count += doTraversalToCountLeaf(n->children[i]);
        }
    }
    return count;
}
  
int countLeaf(SNode *n)
{
    if(n == NULL)
        return 0;
    return doTraversalToCountLeaf(n);
}
  
int doTraversal(SNode *n, char* str, int idx,char* text)
{
    if(n == NULL)
    {
        return -1;
    }
    int res = -1;
    if(n->start != -1)
    {
        res = traverseEdge(str, idx, n->start, *(n->end),text);
        if(res == -1)
            return -1;
        if(res == 1) 
        {
            if(n->suffixIndex > -1){
                printf("\nOrder count: 1");
                test2[ind++] = n->suffixIndex;
            }
            else
                printf("\nOrder count: %d", countLeaf(n));
            return 1;
        }
    }
    idx = idx + edgeLength(n);
    if(n->children[str[idx]] != NULL)
        return doTraversal(n->children[str[idx]], str, idx,text);
    else
        return -1;  // no match
}
void checkForSubString(char* str,SNode* root,char* text,int* pos)
{
    test2 = pos;
    int res = doTraversal(root, str, 0,text);
    test2[ind] = -1;
    if(res == 1){
        ind = 0;
    }
    else{
        printf("\n%s is NOT ordered yet\n", str);
    }
}