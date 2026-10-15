#!/usr/bin/env python3
"""第02讲：用真实参数计算普通卷积与 Depthwise 卷积 MAC/输出形状。"""
import argparse,json
def conv(h,w,ci,co,k,stride,pad,groups):
    if min(h,w,ci,co,k,stride,groups)<=0 or pad<0:raise ValueError("invalid dimensions")
    if ci%groups or co%groups:raise ValueError("channels must be divisible by groups")
    oh=(h+2*pad-k)//stride+1;ow=(w+2*pad-k)//stride+1
    if min(oh,ow)<=0:raise ValueError("kernel larger than padded input")
    return {"output":[oh,ow,co],"mac":oh*ow*co*(ci//groups)*k*k,"parameters":co*(ci//groups)*k*k}
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key,default in (("height",224),("width",224),("in-channels",32),("out-channels",64),("kernel",3),("stride",1),("padding",1)):
        p.add_argument("--"+key,type=int,default=default)
    a=p.parse_args();h,w,ci,co,k,s,pad=a.height,a.width,a.in_channels,a.out_channels,a.kernel,a.stride,a.padding
    regular=conv(h,w,ci,co,k,s,pad,1)
    depth=conv(h,w,ci,ci,k,s,pad,ci)
    point=conv(depth["output"][0],depth["output"][1],ci,co,1,1,0,1)
    efficient=depth["mac"]+point["mac"]
    print(json.dumps({"standard_conv":regular,"depthwise":depth,"pointwise":point,
                      "depthwise_separable_mac":efficient,"mac_ratio_standard_div_separable":regular["mac"]/efficient},indent=2))
if __name__=="__main__":main()
