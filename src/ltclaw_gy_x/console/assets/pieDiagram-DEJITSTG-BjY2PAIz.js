import{j as Z,s as H,k as Q,l as Y,K as tt,J as et,_ as s,o as w,m as at,a0 as it,ao as rt,ap as st,aq as G,ar as ot,p as nt,U as lt,as as ct,a1 as dt}from"./ui-vendor-CzoTwiLl.js";import{p as pt}from"./chunk-4BX2VUAB-BdVyeUT4.js";import{p as gt}from"./wardley-RL74JXVD-Ci9eg614.js";import"./react-vendor-BCTGOMwx.js";import"./utils-vendor-5AggcM3O.js";import"./markdown-vendor-CRx90O4p.js";var ht=dt.pie,C={sections:new Map,showData:!1},u=C.sections,D=C.showData,ut=structuredClone(ht),ft=s(()=>structuredClone(ut),"getConfig"),mt=s(()=>{u=new Map,D=C.showData,lt()},"clear"),vt=s(({label:t,value:a})=>{if(a<0)throw new Error(`"${t}" has invalid value: ${a}. Negative values are not allowed in pie charts. All slice values must be >= 0.`);u.has(t)||(u.set(t,a),w.debug(`added new section: ${t}, with value: ${a}`))},"addSection"),xt=s(()=>u,"getSections"),St=s(t=>{D=t},"setShowData"),wt=s(()=>D,"getShowData"),L={getConfig:ft,clear:mt,setDiagramTitle:et,getDiagramTitle:tt,setAccTitle:Y,getAccTitle:Q,setAccDescription:H,getAccDescription:Z,addSection:vt,getSections:xt,setShowData:St,getShowData:wt},Ct=s((t,a)=>{pt(t,a),a.setShowData(t.showData),t.sections.map(a.addSection)},"populateDb"),Dt={parse:s(async t=>{const a=await gt("pie",t);w.debug(a),Ct(a,L)},"parse")},$t=s(t=>`
  .pieCircle{
    stroke: ${t.pieStrokeColor};
    stroke-width : ${t.pieStrokeWidth};
    opacity : ${t.pieOpacity};
  }
  .pieOuterCircle{
    stroke: ${t.pieOuterStrokeColor};
    stroke-width: ${t.pieOuterStrokeWidth};
    fill: none;
  }
  .pieTitleText {
    text-anchor: middle;
    font-size: ${t.pieTitleTextSize};
    fill: ${t.pieTitleTextColor};
    font-family: ${t.fontFamily};
  }
  .slice {
    font-family: ${t.fontFamily};
    fill: ${t.pieSectionTextColor};
    font-size:${t.pieSectionTextSize};
    // fill: white;
  }
  .legend text {
    fill: ${t.pieLegendTextColor};
    font-family: ${t.fontFamily};
    font-size: ${t.pieLegendTextSize};
  }
`,"getStyles"),yt=$t,Tt=s(t=>{const a=[...t.values()].reduce((r,n)=>r+n,0),$=[...t.entries()].map(([r,n])=>({label:r,value:n})).filter(r=>r.value/a*100>=1);return ct().value(r=>r.value).sort(null)($)},"createPieArcs"),At=s((t,a,$,y)=>{var F;w.debug(`rendering pie chart
`+t);const r=y.db,n=at(),T=it(r.getConfig(),n.pie),A=40,o=18,p=4,c=450,d=c,f=rt(a),l=f.append("g");l.attr("transform","translate("+d/2+","+c/2+")");const{themeVariables:i}=n;let[_]=st(i.pieOuterStrokeWidth);_??(_=2);const b=T.textPosition,g=Math.min(d,c)/2-A,B=G().innerRadius(0).outerRadius(g),O=G().innerRadius(g*b).outerRadius(g*b);l.append("circle").attr("cx",0).attr("cy",0).attr("r",g+_/2).attr("class","pieOuterCircle");const h=r.getSections(),P=Tt(h),I=[i.pie1,i.pie2,i.pie3,i.pie4,i.pie5,i.pie6,i.pie7,i.pie8,i.pie9,i.pie10,i.pie11,i.pie12];let m=0;h.forEach(e=>{m+=e});const k=P.filter(e=>(e.data.value/m*100).toFixed(0)!=="0"),v=ot(I).domain([...h.keys()]);l.selectAll("mySlices").data(k).enter().append("path").attr("d",B).attr("fill",e=>v(e.data.label)).attr("class","pieCircle"),l.selectAll("mySlices").data(k).enter().append("text").text(e=>(e.data.value/m*100).toFixed(0)+"%").attr("transform",e=>"translate("+O.centroid(e)+")").style("text-anchor","middle").attr("class","slice");const N=l.append("text").text(r.getDiagramTitle()).attr("x",0).attr("y",-400/2).attr("class","pieTitleText"),E=[...h.entries()].map(([e,S])=>({label:e,value:S})),x=l.selectAll(".legend").data(E).enter().append("g").attr("class","legend").attr("transform",(e,S)=>{const M=o+p,K=M*E.length/2,V=12*o,X=S*M-K;return"translate("+V+","+X+")"});x.append("rect").attr("width",o).attr("height",o).style("fill",e=>v(e.label)).style("stroke",e=>v(e.label)),x.append("text").attr("x",o+p).attr("y",o-p).text(e=>r.getShowData()?`${e.label} [${e.value}]`:e.label);const U=Math.max(...x.selectAll("text").nodes().map(e=>(e==null?void 0:e.getBoundingClientRect().width)??0)),j=d+A+o+p+U,R=((F=N.node())==null?void 0:F.getBoundingClientRect().width)??0,q=d/2-R/2,J=d/2+R/2,W=Math.min(0,q),z=Math.max(j,J)-W;f.attr("viewBox",`${W} 0 ${z} ${c}`),nt(f,c,z,T.useMaxWidth)},"draw"),_t={draw:At},Mt={parser:Dt,db:L,renderer:_t,styles:yt};export{Mt as diagram};
