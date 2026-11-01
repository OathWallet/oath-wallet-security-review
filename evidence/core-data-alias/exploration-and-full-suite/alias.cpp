#include <TrustWalletCore/TWData.h>
#include <cstdio>
#include <cstring>
#include <vector>
int main(int argc,char** argv) {
    if(argc!=2) return 2;
    std::vector<unsigned char> original(32);
    for(size_t i=0;i<original.size();++i) original[i]=static_cast<unsigned char>(i+1);
    auto* data=TWDataCreateWithBytes(original.data(),original.size());
    if(std::strcmp(argv[1],"self")==0) TWDataAppendData(data,data);
    else if(std::strcmp(argv[1],"alias")==0) TWDataAppendBytes(data,TWDataBytes(data),TWDataSize(data));
    else return 2;
    if(TWDataSize(data)!=64) return 3;
    for(size_t i=0;i<64;++i) if(TWDataBytes(data)[i]!=original[i%32]) return 4;
    TWDataDelete(data);std::puts("32-byte append matches original twice");return 0;
}
