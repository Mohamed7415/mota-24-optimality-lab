/* Exhaustive finite-state check of Ruffle v0.7.1's AVM RNG at level 1.
 * Algorithm port/reference: ruffle-rs/ruffle core/src/avm_rng.rs (MIT/Apache-2.0).
 * All operations are unsigned, including an explicit arithmetic right shift,
 * to avoid C signed-overflow or negative-shift implementation assumptions.
 */
#include <stdint.h>
#include <stdio.h>
#include <inttypes.h>
#include <time.h>
#include <stdlib.h>
#include <string.h>
static uint32_t sar(uint32_t x,unsigned n){return (x>>n)|((x&0x80000000u)?(~0u<<(32-n)):0u);}
static uint32_t next_state(uint32_t x){return (x>>1)^((x&1u)?0x48000000u:0u);}
static uint32_t output(uint32_t state){
 uint32_t s=state*71u;s=((s<<13)^s)-sar(s,21);
 uint32_t r=s*s;r=r*15731u+789221u;r=r*s+1376312589u;r&=0x7fffffffu;r+=s;
 r=((r<<13)^r)-sar(r,21);return (r&0x7fffffffu)%200u;
}
int main(int argc,char **argv){
 if(argc==4 && strcmp(argv[1],"--vectors")==0){
  uint32_t seed=(uint32_t)strtoull(argv[2],0,0),state=0;unsigned n=(unsigned)strtoul(argv[3],0,0);
  if(n>1000000)return 2;
  printf("[");
  for(unsigned i=0;i<n;i++){if(state==0)state=seed;state=next_state(state);printf("%s%u",i?",":"",output(state));}
  puts("]");return 0;
 }
 uint64_t start=1,end=0x80000000ull;if(argc==3){start=strtoull(argv[1],0,0);end=strtoull(argv[2],0,0);}
 if(start<1||start>=end||end>0x80000000ull)return 2;
 uint64_t hist[65]={0};unsigned max=0;uint32_t witness=0;clock_t begun=clock();
 for(uint64_t i=start;i<end;i++){
  uint32_t s=(uint32_t)i;unsigned run=0;
  while(output(s)<=1u){run++;if(run>=64)return 3;s=next_state(s);}
  hist[run]++;if(run>max){max=run;witness=(uint32_t)i;}
 }
 printf("{\"startStateInclusive\":%" PRIu64 ",\"endStateExclusive\":%" PRIu64 ",\"statesChecked\":%" PRIu64 ",\"maxConsecutiveCritical\":%u,\"witnessState\":%u,\"zeroStateOutput\":%u,\"runLengthHistogram\":[",start,end,end-start,max,witness,output(0));
 for(unsigned i=0;i<=max;i++)printf("%s%" PRIu64,i?",":"",hist[i]);
 printf("],\"elapsedCPUSeconds\":%.6f,\"complete\":true}\n",(double)(clock()-begun)/CLOCKS_PER_SEC);return 0;
}
