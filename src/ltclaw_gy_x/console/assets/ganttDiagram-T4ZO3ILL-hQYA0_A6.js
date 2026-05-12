import{g as re,s as ne,t as ce,q as oe,b as le,c as ue,_ as c,d as Z,e as kt,P as de,Q as fe,S as he,f as ke,T as me,U as ye,l as j,V as ge,W as Nt,X as Yt,Y as pe,Z as ve,$ as Te,a0 as xe,a1 as be,a2 as we,a3 as _e,a4 as Bt,a5 as zt,a6 as qt,a7 as Xt,a8 as Ut,a9 as Ce,m as De,k as Se,A as Ee,u as Ie}from"./ui-vendor-DAkP66dV.js";import{d as A,x as Ae,a as Fe,b as Le,y as Me}from"./utils-vendor-OLtI9tkA.js";import"./react-vendor-BCTGOMwx.js";import"./markdown-vendor-CRx90O4p.js";var wt=(function(){var t=c(function(k,o,l,d){for(l=l||{},d=k.length;d--;l[k[d]]=o);return l},"o"),i=[6,8,10,12,13,14,15,16,17,18,20,21,22,23,24,25,26,27,28,29,30,31,33,35,36,38,40],r=[1,26],a=[1,27],n=[1,28],f=[1,29],g=[1,30],S=[1,31],L=[1,32],Y=[1,33],D=[1,34],M=[1,9],B=[1,10],R=[1,11],W=[1,12],_=[1,13],tt=[1,14],et=[1,15],st=[1,16],it=[1,19],H=[1,20],at=[1,21],rt=[1,22],nt=[1,23],ct=[1,25],m=[1,35],T={trace:c(function(){},"trace"),yy:{},symbols_:{error:2,start:3,gantt:4,document:5,EOF:6,line:7,SPACE:8,statement:9,NL:10,weekday:11,weekday_monday:12,weekday_tuesday:13,weekday_wednesday:14,weekday_thursday:15,weekday_friday:16,weekday_saturday:17,weekday_sunday:18,weekend:19,weekend_friday:20,weekend_saturday:21,dateFormat:22,inclusiveEndDates:23,topAxis:24,axisFormat:25,tickInterval:26,excludes:27,includes:28,todayMarker:29,title:30,acc_title:31,acc_title_value:32,acc_descr:33,acc_descr_value:34,acc_descr_multiline_value:35,section:36,clickStatement:37,taskTxt:38,taskData:39,click:40,callbackname:41,callbackargs:42,href:43,clickStatementDebug:44,$accept:0,$end:1},terminals_:{2:"error",4:"gantt",6:"EOF",8:"SPACE",10:"NL",12:"weekday_monday",13:"weekday_tuesday",14:"weekday_wednesday",15:"weekday_thursday",16:"weekday_friday",17:"weekday_saturday",18:"weekday_sunday",20:"weekend_friday",21:"weekend_saturday",22:"dateFormat",23:"inclusiveEndDates",24:"topAxis",25:"axisFormat",26:"tickInterval",27:"excludes",28:"includes",29:"todayMarker",30:"title",31:"acc_title",32:"acc_title_value",33:"acc_descr",34:"acc_descr_value",35:"acc_descr_multiline_value",36:"section",38:"taskTxt",39:"taskData",40:"click",41:"callbackname",42:"callbackargs",43:"href"},productions_:[0,[3,3],[5,0],[5,2],[7,2],[7,1],[7,1],[7,1],[11,1],[11,1],[11,1],[11,1],[11,1],[11,1],[11,1],[19,1],[19,1],[9,1],[9,1],[9,1],[9,1],[9,1],[9,1],[9,1],[9,1],[9,1],[9,1],[9,1],[9,2],[9,2],[9,1],[9,1],[9,1],[9,2],[37,2],[37,3],[37,3],[37,4],[37,3],[37,4],[37,2],[44,2],[44,3],[44,3],[44,4],[44,3],[44,4],[44,2]],performAction:c(function(o,l,d,u,y,s,E){var e=s.length-1;switch(y){case 1:return s[e-1];case 2:this.$=[];break;case 3:s[e-1].push(s[e]),this.$=s[e-1];break;case 4:case 5:this.$=s[e];break;case 6:case 7:this.$=[];break;case 8:u.setWeekday("monday");break;case 9:u.setWeekday("tuesday");break;case 10:u.setWeekday("wednesday");break;case 11:u.setWeekday("thursday");break;case 12:u.setWeekday("friday");break;case 13:u.setWeekday("saturday");break;case 14:u.setWeekday("sunday");break;case 15:u.setWeekend("friday");break;case 16:u.setWeekend("saturday");break;case 17:u.setDateFormat(s[e].substr(11)),this.$=s[e].substr(11);break;case 18:u.enableInclusiveEndDates(),this.$=s[e].substr(18);break;case 19:u.TopAxis(),this.$=s[e].substr(8);break;case 20:u.setAxisFormat(s[e].substr(11)),this.$=s[e].substr(11);break;case 21:u.setTickInterval(s[e].substr(13)),this.$=s[e].substr(13);break;case 22:u.setExcludes(s[e].substr(9)),this.$=s[e].substr(9);break;case 23:u.setIncludes(s[e].substr(9)),this.$=s[e].substr(9);break;case 24:u.setTodayMarker(s[e].substr(12)),this.$=s[e].substr(12);break;case 27:u.setDiagramTitle(s[e].substr(6)),this.$=s[e].substr(6);break;case 28:this.$=s[e].trim(),u.setAccTitle(this.$);break;case 29:case 30:this.$=s[e].trim(),u.setAccDescription(this.$);break;case 31:u.addSection(s[e].substr(8)),this.$=s[e].substr(8);break;case 33:u.addTask(s[e-1],s[e]),this.$="task";break;case 34:this.$=s[e-1],u.setClickEvent(s[e-1],s[e],null);break;case 35:this.$=s[e-2],u.setClickEvent(s[e-2],s[e-1],s[e]);break;case 36:this.$=s[e-2],u.setClickEvent(s[e-2],s[e-1],null),u.setLink(s[e-2],s[e]);break;case 37:this.$=s[e-3],u.setClickEvent(s[e-3],s[e-2],s[e-1]),u.setLink(s[e-3],s[e]);break;case 38:this.$=s[e-2],u.setClickEvent(s[e-2],s[e],null),u.setLink(s[e-2],s[e-1]);break;case 39:this.$=s[e-3],u.setClickEvent(s[e-3],s[e-1],s[e]),u.setLink(s[e-3],s[e-2]);break;case 40:this.$=s[e-1],u.setLink(s[e-1],s[e]);break;case 41:case 47:this.$=s[e-1]+" "+s[e];break;case 42:case 43:case 45:this.$=s[e-2]+" "+s[e-1]+" "+s[e];break;case 44:case 46:this.$=s[e-3]+" "+s[e-2]+" "+s[e-1]+" "+s[e];break}},"anonymous"),table:[{3:1,4:[1,2]},{1:[3]},t(i,[2,2],{5:3}),{6:[1,4],7:5,8:[1,6],9:7,10:[1,8],11:17,12:r,13:a,14:n,15:f,16:g,17:S,18:L,19:18,20:Y,21:D,22:M,23:B,24:R,25:W,26:_,27:tt,28:et,29:st,30:it,31:H,33:at,35:rt,36:nt,37:24,38:ct,40:m},t(i,[2,7],{1:[2,1]}),t(i,[2,3]),{9:36,11:17,12:r,13:a,14:n,15:f,16:g,17:S,18:L,19:18,20:Y,21:D,22:M,23:B,24:R,25:W,26:_,27:tt,28:et,29:st,30:it,31:H,33:at,35:rt,36:nt,37:24,38:ct,40:m},t(i,[2,5]),t(i,[2,6]),t(i,[2,17]),t(i,[2,18]),t(i,[2,19]),t(i,[2,20]),t(i,[2,21]),t(i,[2,22]),t(i,[2,23]),t(i,[2,24]),t(i,[2,25]),t(i,[2,26]),t(i,[2,27]),{32:[1,37]},{34:[1,38]},t(i,[2,30]),t(i,[2,31]),t(i,[2,32]),{39:[1,39]},t(i,[2,8]),t(i,[2,9]),t(i,[2,10]),t(i,[2,11]),t(i,[2,12]),t(i,[2,13]),t(i,[2,14]),t(i,[2,15]),t(i,[2,16]),{41:[1,40],43:[1,41]},t(i,[2,4]),t(i,[2,28]),t(i,[2,29]),t(i,[2,33]),t(i,[2,34],{42:[1,42],43:[1,43]}),t(i,[2,40],{41:[1,44]}),t(i,[2,35],{43:[1,45]}),t(i,[2,36]),t(i,[2,38],{42:[1,46]}),t(i,[2,37]),t(i,[2,39])],defaultActions:{},parseError:c(function(o,l){if(l.recoverable)this.trace(o);else{var d=new Error(o);throw d.hash=l,d}},"parseError"),parse:c(function(o){var l=this,d=[0],u=[],y=[null],s=[],E=this.table,e="",h=0,C=0,w=2,b=1,F=s.slice.call(arguments,1),v=Object.create(this.lexer),z={yy:{}};for(var ot in this.yy)Object.prototype.hasOwnProperty.call(this.yy,ot)&&(z.yy[ot]=this.yy[ot]);v.setInput(o,z.yy),z.yy.lexer=v,z.yy.parser=this,typeof v.yylloc>"u"&&(v.yylloc={});var vt=v.yylloc;s.push(vt);var ie=v.options&&v.options.ranges;typeof z.yy.parseError=="function"?this.parseError=z.yy.parseError:this.parseError=Object.getPrototypeOf(this).parseError;function ae(V){d.length=d.length-2*V,y.length=y.length-V,s.length=s.length-V}c(ae,"popStack");function Wt(){var V;return V=u.pop()||v.lex()||b,typeof V!="number"&&(V instanceof Array&&(u=V,V=u.pop()),V=l.symbols_[V]||V),V}c(Wt,"lex");for(var O,U,P,Tt,K={},ft,q,Pt,ht;;){if(U=d[d.length-1],this.defaultActions[U]?P=this.defaultActions[U]:((O===null||typeof O>"u")&&(O=Wt()),P=E[U]&&E[U][O]),typeof P>"u"||!P.length||!P[0]){var xt="";ht=[];for(ft in E[U])this.terminals_[ft]&&ft>w&&ht.push("'"+this.terminals_[ft]+"'");v.showPosition?xt="Parse error on line "+(h+1)+`:
`+v.showPosition()+`
Expecting `+ht.join(", ")+", got '"+(this.terminals_[O]||O)+"'":xt="Parse error on line "+(h+1)+": Unexpected "+(O==b?"end of input":"'"+(this.terminals_[O]||O)+"'"),this.parseError(xt,{text:v.match,token:this.terminals_[O]||O,line:v.yylineno,loc:vt,expected:ht})}if(P[0]instanceof Array&&P.length>1)throw new Error("Parse Error: multiple actions possible at state: "+U+", token: "+O);switch(P[0]){case 1:d.push(O),y.push(v.yytext),s.push(v.yylloc),d.push(P[1]),O=null,C=v.yyleng,e=v.yytext,h=v.yylineno,vt=v.yylloc;break;case 2:if(q=this.productions_[P[1]][1],K.$=y[y.length-q],K._$={first_line:s[s.length-(q||1)].first_line,last_line:s[s.length-1].last_line,first_column:s[s.length-(q||1)].first_column,last_column:s[s.length-1].last_column},ie&&(K._$.range=[s[s.length-(q||1)].range[0],s[s.length-1].range[1]]),Tt=this.performAction.apply(K,[e,C,h,z.yy,P[1],y,s].concat(F)),typeof Tt<"u")return Tt;q&&(d=d.slice(0,-1*q*2),y=y.slice(0,-1*q),s=s.slice(0,-1*q)),d.push(this.productions_[P[1]][0]),y.push(K.$),s.push(K._$),Pt=E[d[d.length-2]][d[d.length-1]],d.push(Pt);break;case 3:return!0}}return!0},"parse")},x=(function(){var k={EOF:1,parseError:c(function(l,d){if(this.yy.parser)this.yy.parser.parseError(l,d);else throw new Error(l)},"parseError"),setInput:c(function(o,l){return this.yy=l||this.yy||{},this._input=o,this._more=this._backtrack=this.done=!1,this.yylineno=this.yyleng=0,this.yytext=this.matched=this.match="",this.conditionStack=["INITIAL"],this.yylloc={first_line:1,first_column:0,last_line:1,last_column:0},this.options.ranges&&(this.yylloc.range=[0,0]),this.offset=0,this},"setInput"),input:c(function(){var o=this._input[0];this.yytext+=o,this.yyleng++,this.offset++,this.match+=o,this.matched+=o;var l=o.match(/(?:\r\n?|\n).*/g);return l?(this.yylineno++,this.yylloc.last_line++):this.yylloc.last_column++,this.options.ranges&&this.yylloc.range[1]++,this._input=this._input.slice(1),o},"input"),unput:c(function(o){var l=o.length,d=o.split(/(?:\r\n?|\n)/g);this._input=o+this._input,this.yytext=this.yytext.substr(0,this.yytext.length-l),this.offset-=l;var u=this.match.split(/(?:\r\n?|\n)/g);this.match=this.match.substr(0,this.match.length-1),this.matched=this.matched.substr(0,this.matched.length-1),d.length-1&&(this.yylineno-=d.length-1);var y=this.yylloc.range;return this.yylloc={first_line:this.yylloc.first_line,last_line:this.yylineno+1,first_column:this.yylloc.first_column,last_column:d?(d.length===u.length?this.yylloc.first_column:0)+u[u.length-d.length].length-d[0].length:this.yylloc.first_column-l},this.options.ranges&&(this.yylloc.range=[y[0],y[0]+this.yyleng-l]),this.yyleng=this.yytext.length,this},"unput"),more:c(function(){return this._more=!0,this},"more"),reject:c(function(){if(this.options.backtrack_lexer)this._backtrack=!0;else return this.parseError("Lexical error on line "+(this.yylineno+1)+`. You can only invoke reject() in the lexer when the lexer is of the backtracking persuasion (options.backtrack_lexer = true).
`+this.showPosition(),{text:"",token:null,line:this.yylineno});return this},"reject"),less:c(function(o){this.unput(this.match.slice(o))},"less"),pastInput:c(function(){var o=this.matched.substr(0,this.matched.length-this.match.length);return(o.length>20?"...":"")+o.substr(-20).replace(/\n/g,"")},"pastInput"),upcomingInput:c(function(){var o=this.match;return o.length<20&&(o+=this._input.substr(0,20-o.length)),(o.substr(0,20)+(o.length>20?"...":"")).replace(/\n/g,"")},"upcomingInput"),showPosition:c(function(){var o=this.pastInput(),l=new Array(o.length+1).join("-");return o+this.upcomingInput()+`
`+l+"^"},"showPosition"),test_match:c(function(o,l){var d,u,y;if(this.options.backtrack_lexer&&(y={yylineno:this.yylineno,yylloc:{first_line:this.yylloc.first_line,last_line:this.last_line,first_column:this.yylloc.first_column,last_column:this.yylloc.last_column},yytext:this.yytext,match:this.match,matches:this.matches,matched:this.matched,yyleng:this.yyleng,offset:this.offset,_more:this._more,_input:this._input,yy:this.yy,conditionStack:this.conditionStack.slice(0),done:this.done},this.options.ranges&&(y.yylloc.range=this.yylloc.range.slice(0))),u=o[0].match(/(?:\r\n?|\n).*/g),u&&(this.yylineno+=u.length),this.yylloc={first_line:this.yylloc.last_line,last_line:this.yylineno+1,first_column:this.yylloc.last_column,last_column:u?u[u.length-1].length-u[u.length-1].match(/\r?\n?/)[0].length:this.yylloc.last_column+o[0].length},this.yytext+=o[0],this.match+=o[0],this.matches=o,this.yyleng=this.yytext.length,this.options.ranges&&(this.yylloc.range=[this.offset,this.offset+=this.yyleng]),this._more=!1,this._backtrack=!1,this._input=this._input.slice(o[0].length),this.matched+=o[0],d=this.performAction.call(this,this.yy,this,l,this.conditionStack[this.conditionStack.length-1]),this.done&&this._input&&(this.done=!1),d)return d;if(this._backtrack){for(var s in y)this[s]=y[s];return!1}return!1},"test_match"),next:c(function(){if(this.done)return this.EOF;this._input||(this.done=!0);var o,l,d,u;this._more||(this.yytext="",this.match="");for(var y=this._currentRules(),s=0;s<y.length;s++)if(d=this._input.match(this.rules[y[s]]),d&&(!l||d[0].length>l[0].length)){if(l=d,u=s,this.options.backtrack_lexer){if(o=this.test_match(d,y[s]),o!==!1)return o;if(this._backtrack){l=!1;continue}else return!1}else if(!this.options.flex)break}return l?(o=this.test_match(l,y[u]),o!==!1?o:!1):this._input===""?this.EOF:this.parseError("Lexical error on line "+(this.yylineno+1)+`. Unrecognized text.
`+this.showPosition(),{text:"",token:null,line:this.yylineno})},"next"),lex:c(function(){var l=this.next();return l||this.lex()},"lex"),begin:c(function(l){this.conditionStack.push(l)},"begin"),popState:c(function(){var l=this.conditionStack.length-1;return l>0?this.conditionStack.pop():this.conditionStack[0]},"popState"),_currentRules:c(function(){return this.conditionStack.length&&this.conditionStack[this.conditionStack.length-1]?this.conditions[this.conditionStack[this.conditionStack.length-1]].rules:this.conditions.INITIAL.rules},"_currentRules"),topState:c(function(l){return l=this.conditionStack.length-1-Math.abs(l||0),l>=0?this.conditionStack[l]:"INITIAL"},"topState"),pushState:c(function(l){this.begin(l)},"pushState"),stateStackSize:c(function(){return this.conditionStack.length},"stateStackSize"),options:{"case-insensitive":!0},performAction:c(function(l,d,u,y){switch(u){case 0:return this.begin("open_directive"),"open_directive";case 1:return this.begin("acc_title"),31;case 2:return this.popState(),"acc_title_value";case 3:return this.begin("acc_descr"),33;case 4:return this.popState(),"acc_descr_value";case 5:this.begin("acc_descr_multiline");break;case 6:this.popState();break;case 7:return"acc_descr_multiline_value";case 8:break;case 9:break;case 10:break;case 11:return 10;case 12:break;case 13:break;case 14:this.begin("href");break;case 15:this.popState();break;case 16:return 43;case 17:this.begin("callbackname");break;case 18:this.popState();break;case 19:this.popState(),this.begin("callbackargs");break;case 20:return 41;case 21:this.popState();break;case 22:return 42;case 23:this.begin("click");break;case 24:this.popState();break;case 25:return 40;case 26:return 4;case 27:return 22;case 28:return 23;case 29:return 24;case 30:return 25;case 31:return 26;case 32:return 28;case 33:return 27;case 34:return 29;case 35:return 12;case 36:return 13;case 37:return 14;case 38:return 15;case 39:return 16;case 40:return 17;case 41:return 18;case 42:return 20;case 43:return 21;case 44:return"date";case 45:return 30;case 46:return"accDescription";case 47:return 36;case 48:return 38;case 49:return 39;case 50:return":";case 51:return 6;case 52:return"INVALID"}},"anonymous"),rules:[/^(?:%%\{)/i,/^(?:accTitle\s*:\s*)/i,/^(?:(?!\n||)*[^\n]*)/i,/^(?:accDescr\s*:\s*)/i,/^(?:(?!\n||)*[^\n]*)/i,/^(?:accDescr\s*\{\s*)/i,/^(?:[\}])/i,/^(?:[^\}]*)/i,/^(?:%%(?!\{)*[^\n]*)/i,/^(?:[^\}]%%*[^\n]*)/i,/^(?:%%*[^\n]*[\n]*)/i,/^(?:[\n]+)/i,/^(?:\s+)/i,/^(?:%[^\n]*)/i,/^(?:href[\s]+["])/i,/^(?:["])/i,/^(?:[^"]*)/i,/^(?:call[\s]+)/i,/^(?:\([\s]*\))/i,/^(?:\()/i,/^(?:[^(]*)/i,/^(?:\))/i,/^(?:[^)]*)/i,/^(?:click[\s]+)/i,/^(?:[\s\n])/i,/^(?:[^\s\n]*)/i,/^(?:gantt\b)/i,/^(?:dateFormat\s[^#\n;]+)/i,/^(?:inclusiveEndDates\b)/i,/^(?:topAxis\b)/i,/^(?:axisFormat\s[^#\n;]+)/i,/^(?:tickInterval\s[^#\n;]+)/i,/^(?:includes\s[^#\n;]+)/i,/^(?:excludes\s[^#\n;]+)/i,/^(?:todayMarker\s[^\n;]+)/i,/^(?:weekday\s+monday\b)/i,/^(?:weekday\s+tuesday\b)/i,/^(?:weekday\s+wednesday\b)/i,/^(?:weekday\s+thursday\b)/i,/^(?:weekday\s+friday\b)/i,/^(?:weekday\s+saturday\b)/i,/^(?:weekday\s+sunday\b)/i,/^(?:weekend\s+friday\b)/i,/^(?:weekend\s+saturday\b)/i,/^(?:\d\d\d\d-\d\d-\d\d\b)/i,/^(?:title\s[^\n]+)/i,/^(?:accDescription\s[^#\n;]+)/i,/^(?:section\s[^\n]+)/i,/^(?:[^:\n]+)/i,/^(?::[^#\n;]+)/i,/^(?::)/i,/^(?:$)/i,/^(?:.)/i],conditions:{acc_descr_multiline:{rules:[6,7],inclusive:!1},acc_descr:{rules:[4],inclusive:!1},acc_title:{rules:[2],inclusive:!1},callbackargs:{rules:[21,22],inclusive:!1},callbackname:{rules:[18,19,20],inclusive:!1},href:{rules:[15,16],inclusive:!1},click:{rules:[24,25],inclusive:!1},INITIAL:{rules:[0,1,3,5,8,9,10,11,12,13,14,17,23,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52],inclusive:!0}}};return k})();T.lexer=x;function p(){this.yy={}}return c(p,"Parser"),p.prototype=T,T.Parser=p,new p})();wt.parser=wt;var Oe=wt;A.extend(Ae);A.extend(Fe);A.extend(Le);var jt={friday:5,saturday:6},N="",St="",Et=void 0,It="",lt=[],ut=[],At=new Map,Ft=[],gt=[],$="",Lt="",Kt=["active","done","crit","milestone","vert"],Mt=[],Q="",dt=!1,Ot=!1,Vt="sunday",pt="saturday",_t=0,Ve=c(function(){Ft=[],gt=[],$="",Mt=[],mt=0,Dt=void 0,yt=void 0,I=[],N="",St="",Lt="",Et=void 0,It="",lt=[],ut=[],dt=!1,Ot=!1,_t=0,At=new Map,Q="",Ee(),Vt="sunday",pt="saturday"},"clear"),Re=c(function(t){Q=t},"setDiagramId"),We=c(function(t){St=t},"setAxisFormat"),Pe=c(function(){return St},"getAxisFormat"),Ne=c(function(t){Et=t},"setTickInterval"),Ye=c(function(){return Et},"getTickInterval"),Be=c(function(t){It=t},"setTodayMarker"),ze=c(function(){return It},"getTodayMarker"),qe=c(function(t){N=t},"setDateFormat"),Xe=c(function(){dt=!0},"enableInclusiveEndDates"),Ue=c(function(){return dt},"endDatesAreInclusive"),je=c(function(){Ot=!0},"enableTopAxis"),Ge=c(function(){return Ot},"topAxisEnabled"),He=c(function(t){Lt=t},"setDisplayMode"),Ke=c(function(){return Lt},"getDisplayMode"),Qe=c(function(){return N},"getDateFormat"),Ze=c(function(t){lt=t.toLowerCase().split(/[\s,]+/)},"setIncludes"),Je=c(function(){return lt},"getIncludes"),$e=c(function(t){ut=t.toLowerCase().split(/[\s,]+/)},"setExcludes"),ts=c(function(){return ut},"getExcludes"),es=c(function(){return At},"getLinks"),ss=c(function(t){$=t,Ft.push(t)},"addSection"),is=c(function(){return Ft},"getSections"),as=c(function(){let t=Gt();const i=10;let r=0;for(;!t&&r<i;)t=Gt(),r++;return gt=I,gt},"getTasks"),Qt=c(function(t,i,r,a){const n=t.format(i.trim()),f=t.format("YYYY-MM-DD");return a.includes(n)||a.includes(f)?!1:r.includes("weekends")&&(t.isoWeekday()===jt[pt]||t.isoWeekday()===jt[pt]+1)||r.includes(t.format("dddd").toLowerCase())?!0:r.includes(n)||r.includes(f)},"isInvalidDate"),rs=c(function(t){Vt=t},"setWeekday"),ns=c(function(){return Vt},"getWeekday"),cs=c(function(t){pt=t},"setWeekend"),Zt=c(function(t,i,r,a){if(!r.length||t.manualEndTime)return;let n;t.startTime instanceof Date?n=A(t.startTime):n=A(t.startTime,i,!0),n=n.add(1,"d");let f;t.endTime instanceof Date?f=A(t.endTime):f=A(t.endTime,i,!0);const[g,S]=os(n,f,i,r,a);t.endTime=g.toDate(),t.renderEndTime=S},"checkTaskDates"),os=c(function(t,i,r,a,n){let f=!1,g=null;for(;t<=i;)f||(g=i.toDate()),f=Qt(t,r,a,n),f&&(i=i.add(1,"d")),t=t.add(1,"d");return[i,g]},"fixTaskDates"),Ct=c(function(t,i,r){if(r=r.trim(),c(S=>{const L=S.trim();return L==="x"||L==="X"},"isTimestampFormat")(i)&&/^\d+$/.test(r))return new Date(Number(r));const f=/^after\s+(?<ids>[\d\w- ]+)/.exec(r);if(f!==null){let S=null;for(const Y of f.groups.ids.split(" ")){let D=G(Y);D!==void 0&&(!S||D.endTime>S.endTime)&&(S=D)}if(S)return S.endTime;const L=new Date;return L.setHours(0,0,0,0),L}let g=A(r,i.trim(),!0);if(g.isValid())return g.toDate();{j.debug("Invalid date:"+r),j.debug("With date format:"+i.trim());const S=new Date(r);if(S===void 0||isNaN(S.getTime())||S.getFullYear()<-1e4||S.getFullYear()>1e4)throw new Error("Invalid date:"+r);return S}},"getStartDate"),Jt=c(function(t){const i=/^(\d+(?:\.\d+)?)([Mdhmswy]|ms)$/.exec(t.trim());return i!==null?[Number.parseFloat(i[1]),i[2]]:[NaN,"ms"]},"parseDuration"),$t=c(function(t,i,r,a=!1){r=r.trim();const f=/^until\s+(?<ids>[\d\w- ]+)/.exec(r);if(f!==null){let D=null;for(const B of f.groups.ids.split(" ")){let R=G(B);R!==void 0&&(!D||R.startTime<D.startTime)&&(D=R)}if(D)return D.startTime;const M=new Date;return M.setHours(0,0,0,0),M}let g=A(r,i.trim(),!0);if(g.isValid())return a&&(g=g.add(1,"d")),g.toDate();let S=A(t);const[L,Y]=Jt(r);if(!Number.isNaN(L)){const D=S.add(L,Y);D.isValid()&&(S=D)}return S.toDate()},"getEndDate"),mt=0,J=c(function(t){return t===void 0?(mt=mt+1,"task"+mt):t},"parseId"),ls=c(function(t,i){let r;i.substr(0,1)===":"?r=i.substr(1,i.length):r=i;const a=r.split(","),n={};Rt(a,n,Kt);for(let g=0;g<a.length;g++)a[g]=a[g].trim();let f="";switch(a.length){case 1:n.id=J(),n.startTime=t.endTime,f=a[0];break;case 2:n.id=J(),n.startTime=Ct(void 0,N,a[0]),f=a[1];break;case 3:n.id=J(a[0]),n.startTime=Ct(void 0,N,a[1]),f=a[2];break}return f&&(n.endTime=$t(n.startTime,N,f,dt),n.manualEndTime=A(f,"YYYY-MM-DD",!0).isValid(),Zt(n,N,ut,lt)),n},"compileData"),us=c(function(t,i){let r;i.substr(0,1)===":"?r=i.substr(1,i.length):r=i;const a=r.split(","),n={};Rt(a,n,Kt);for(let f=0;f<a.length;f++)a[f]=a[f].trim();switch(a.length){case 1:n.id=J(),n.startTime={type:"prevTaskEnd",id:t},n.endTime={data:a[0]};break;case 2:n.id=J(),n.startTime={type:"getStartDate",startData:a[0]},n.endTime={data:a[1]};break;case 3:n.id=J(a[0]),n.startTime={type:"getStartDate",startData:a[1]},n.endTime={data:a[2]};break}return n},"parseData"),Dt,yt,I=[],te={},ds=c(function(t,i){const r={section:$,type:$,processed:!1,manualEndTime:!1,renderEndTime:null,raw:{data:i},task:t,classes:[]},a=us(yt,i);r.raw.startTime=a.startTime,r.raw.endTime=a.endTime,r.id=a.id,r.prevTaskId=yt,r.active=a.active,r.done=a.done,r.crit=a.crit,r.milestone=a.milestone,r.vert=a.vert,r.order=_t,_t++;const n=I.push(r);yt=r.id,te[r.id]=n-1},"addTask"),G=c(function(t){const i=te[t];return I[i]},"findTaskById"),fs=c(function(t,i){const r={section:$,type:$,description:t,task:t,classes:[]},a=ls(Dt,i);r.startTime=a.startTime,r.endTime=a.endTime,r.id=a.id,r.active=a.active,r.done=a.done,r.crit=a.crit,r.milestone=a.milestone,r.vert=a.vert,Dt=r,gt.push(r)},"addTaskOrg"),Gt=c(function(){const t=c(function(r){const a=I[r];let n="";switch(I[r].raw.startTime.type){case"prevTaskEnd":{const f=G(a.prevTaskId);a.startTime=f.endTime;break}case"getStartDate":n=Ct(void 0,N,I[r].raw.startTime.startData),n&&(I[r].startTime=n);break}return I[r].startTime&&(I[r].endTime=$t(I[r].startTime,N,I[r].raw.endTime.data,dt),I[r].endTime&&(I[r].processed=!0,I[r].manualEndTime=A(I[r].raw.endTime.data,"YYYY-MM-DD",!0).isValid(),Zt(I[r],N,ut,lt))),I[r].processed},"compileTask");let i=!0;for(const[r,a]of I.entries())t(r),i=i&&a.processed;return i},"compileTasks"),hs=c(function(t,i){let r=i;Z().securityLevel!=="loose"&&(r=Se.sanitizeUrl(i)),t.split(",").forEach(function(a){G(a)!==void 0&&(se(a,()=>{window.open(r,"_self")}),At.set(a,r))}),ee(t,"clickable")},"setLink"),ee=c(function(t,i){t.split(",").forEach(function(r){let a=G(r);a!==void 0&&a.classes.push(i)})},"setClass"),ks=c(function(t,i,r){if(Z().securityLevel!=="loose"||i===void 0)return;let a=[];if(typeof r=="string"){a=r.split(/,(?=(?:(?:[^"]*"){2})*[^"]*$)/);for(let f=0;f<a.length;f++){let g=a[f].trim();g.startsWith('"')&&g.endsWith('"')&&(g=g.substr(1,g.length-2)),a[f]=g}}a.length===0&&a.push(t),G(t)!==void 0&&se(t,()=>{Ie.runFunc(i,...a)})},"setClickFun"),se=c(function(t,i){Mt.push(function(){const r=Q?`${Q}-${t}`:t,a=document.querySelector(`[id="${r}"]`);a!==null&&a.addEventListener("click",function(){i()})},function(){const r=Q?`${Q}-${t}`:t,a=document.querySelector(`[id="${r}-text"]`);a!==null&&a.addEventListener("click",function(){i()})})},"pushFun"),ms=c(function(t,i,r){t.split(",").forEach(function(a){ks(a,i,r)}),ee(t,"clickable")},"setClickEvent"),ys=c(function(t){Mt.forEach(function(i){i(t)})},"bindFunctions"),gs={getConfig:c(()=>Z().gantt,"getConfig"),clear:Ve,setDateFormat:qe,getDateFormat:Qe,enableInclusiveEndDates:Xe,endDatesAreInclusive:Ue,enableTopAxis:je,topAxisEnabled:Ge,setAxisFormat:We,getAxisFormat:Pe,setTickInterval:Ne,getTickInterval:Ye,setTodayMarker:Be,getTodayMarker:ze,setAccTitle:ue,getAccTitle:le,setDiagramTitle:oe,getDiagramTitle:ce,setDiagramId:Re,setDisplayMode:He,getDisplayMode:Ke,setAccDescription:ne,getAccDescription:re,addSection:ss,getSections:is,getTasks:as,addTask:ds,findTaskById:G,addTaskOrg:fs,setIncludes:Ze,getIncludes:Je,setExcludes:$e,getExcludes:ts,setClickEvent:ms,setLink:hs,getLinks:es,bindFunctions:ys,parseDuration:Jt,isInvalidDate:Qt,setWeekday:rs,getWeekday:ns,setWeekend:cs};function Rt(t,i,r){let a=!0;for(;a;)a=!1,r.forEach(function(n){const f="^\\s*"+n+"\\s*$",g=new RegExp(f);t[0].match(g)&&(i[n]=!0,t.shift(1),a=!0)})}c(Rt,"getTaskTags");A.extend(Me);var ps=c(function(){j.debug("Something is calling, setConf, remove the call")},"setConf"),Ht={monday:_e,tuesday:we,wednesday:be,thursday:xe,friday:Te,saturday:ve,sunday:pe},vs=c((t,i)=>{let r=[...t].map(()=>-1/0),a=[...t].sort((f,g)=>f.startTime-g.startTime||f.order-g.order),n=0;for(const f of a)for(let g=0;g<r.length;g++)if(f.startTime>=r[g]){r[g]=f.endTime,f.order=g+i,g>n&&(n=g);break}return n},"getMaxIntersections"),X,bt=1e4,Ts=c(function(t,i,r,a){const n=Z().gantt;a.db.setDiagramId(i);const f=Z().securityLevel;let g;f==="sandbox"&&(g=kt("#i"+i));const S=f==="sandbox"?kt(g.nodes()[0].contentDocument.body):kt("body"),L=f==="sandbox"?g.nodes()[0].contentDocument:document,Y=L.getElementById(i);X=Y.parentElement.offsetWidth,X===void 0&&(X=1200),n.useWidth!==void 0&&(X=n.useWidth);const D=a.db.getTasks();let M=[];for(const m of D)M.push(m.type);M=ct(M);const B={};let R=2*n.topPadding;if(a.db.getDisplayMode()==="compact"||n.displayMode==="compact"){const m={};for(const x of D)m[x.section]===void 0?m[x.section]=[x]:m[x.section].push(x);let T=0;for(const x of Object.keys(m)){const p=vs(m[x],T)+1;T+=p,R+=p*(n.barHeight+n.barGap),B[x]=p}}else{R+=D.length*(n.barHeight+n.barGap);for(const m of M)B[m]=D.filter(T=>T.type===m).length}Y.setAttribute("viewBox","0 0 "+X+" "+R);const W=S.select(`[id="${i}"]`),_=de().domain([fe(D,function(m){return m.startTime}),he(D,function(m){return m.endTime})]).rangeRound([0,X-n.leftPadding-n.rightPadding]);function tt(m,T){const x=m.startTime,p=T.startTime;let k=0;return x>p?k=1:x<p&&(k=-1),k}c(tt,"taskCompare"),D.sort(tt),et(D,X,R),ke(W,R,X,n.useMaxWidth),W.append("text").text(a.db.getDiagramTitle()).attr("x",X/2).attr("y",n.titleTopMargin).attr("class","titleText");function et(m,T,x){const p=n.barHeight,k=p+n.barGap,o=n.topPadding,l=n.leftPadding,d=me().domain([0,M.length]).range(["#00B9FA","#F95002"]).interpolate(ye);it(k,o,l,T,x,m,a.db.getExcludes(),a.db.getIncludes()),at(l,o,T,x),st(m,k,o,l,p,d,T),rt(k,o),nt(l,o,T,x)}c(et,"makeGantt");function st(m,T,x,p,k,o,l){m.sort((e,h)=>e.vert===h.vert?0:e.vert?1:-1);const u=[...new Set(m.map(e=>e.order))].map(e=>m.find(h=>h.order===e));W.append("g").selectAll("rect").data(u).enter().append("rect").attr("x",0).attr("y",function(e,h){return h=e.order,h*T+x-2}).attr("width",function(){return l-n.rightPadding/2}).attr("height",T).attr("class",function(e){for(const[h,C]of M.entries())if(e.type===C)return"section section"+h%n.numberSectionStyles;return"section section0"}).enter();const y=W.append("g").selectAll("rect").data(m).enter(),s=a.db.getLinks();if(y.append("rect").attr("id",function(e){return i+"-"+e.id}).attr("rx",3).attr("ry",3).attr("x",function(e){return e.milestone?_(e.startTime)+p+.5*(_(e.endTime)-_(e.startTime))-.5*k:_(e.startTime)+p}).attr("y",function(e,h){return h=e.order,e.vert?n.gridLineStartPadding:h*T+x}).attr("width",function(e){return e.milestone?k:e.vert?.08*k:_(e.renderEndTime||e.endTime)-_(e.startTime)}).attr("height",function(e){return e.vert?D.length*(n.barHeight+n.barGap)+n.barHeight*2:k}).attr("transform-origin",function(e,h){return h=e.order,(_(e.startTime)+p+.5*(_(e.endTime)-_(e.startTime))).toString()+"px "+(h*T+x+.5*k).toString()+"px"}).attr("class",function(e){const h="task";let C="";e.classes.length>0&&(C=e.classes.join(" "));let w=0;for(const[F,v]of M.entries())e.type===v&&(w=F%n.numberSectionStyles);let b="";return e.active?e.crit?b+=" activeCrit":b=" active":e.done?e.crit?b=" doneCrit":b=" done":e.crit&&(b+=" crit"),b.length===0&&(b=" task"),e.milestone&&(b=" milestone "+b),e.vert&&(b=" vert "+b),b+=w,b+=" "+C,h+b}),y.append("text").attr("id",function(e){return i+"-"+e.id+"-text"}).text(function(e){return e.task}).attr("font-size",n.fontSize).attr("x",function(e){let h=_(e.startTime),C=_(e.renderEndTime||e.endTime);if(e.milestone&&(h+=.5*(_(e.endTime)-_(e.startTime))-.5*k,C=h+k),e.vert)return _(e.startTime)+p;const w=this.getBBox().width;return w>C-h?C+w+1.5*n.leftPadding>l?h+p-5:C+p+5:(C-h)/2+h+p}).attr("y",function(e,h){return e.vert?n.gridLineStartPadding+D.length*(n.barHeight+n.barGap)+60:(h=e.order,h*T+n.barHeight/2+(n.fontSize/2-2)+x)}).attr("text-height",k).attr("class",function(e){const h=_(e.startTime);let C=_(e.endTime);e.milestone&&(C=h+k);const w=this.getBBox().width;let b="";e.classes.length>0&&(b=e.classes.join(" "));let F=0;for(const[z,ot]of M.entries())e.type===ot&&(F=z%n.numberSectionStyles);let v="";return e.active&&(e.crit?v="activeCritText"+F:v="activeText"+F),e.done?e.crit?v=v+" doneCritText"+F:v=v+" doneText"+F:e.crit&&(v=v+" critText"+F),e.milestone&&(v+=" milestoneText"),e.vert&&(v+=" vertText"),w>C-h?C+w+1.5*n.leftPadding>l?b+" taskTextOutsideLeft taskTextOutside"+F+" "+v:b+" taskTextOutsideRight taskTextOutside"+F+" "+v+" width-"+w:b+" taskText taskText"+F+" "+v+" width-"+w}),Z().securityLevel==="sandbox"){let e;e=kt("#i"+i);const h=e.nodes()[0].contentDocument;y.filter(function(C){return s.has(C.id)}).each(function(C){var w=h.querySelector("#"+CSS.escape(i+"-"+C.id)),b=h.querySelector("#"+CSS.escape(i+"-"+C.id+"-text"));const F=w.parentNode;var v=h.createElement("a");v.setAttribute("xlink:href",s.get(C.id)),v.setAttribute("target","_top"),F.appendChild(v),v.appendChild(w),v.appendChild(b)})}}c(st,"drawRects");function it(m,T,x,p,k,o,l,d){if(l.length===0&&d.length===0)return;let u,y;for(const{startTime:w,endTime:b}of o)(u===void 0||w<u)&&(u=w),(y===void 0||b>y)&&(y=b);if(!u||!y)return;if(A(y).diff(A(u),"year")>5){j.warn("The difference between the min and max time is more than 5 years. This will cause performance issues. Skipping drawing exclude days.");return}const s=a.db.getDateFormat(),E=[];let e=null,h=A(u);for(;h.valueOf()<=y;)a.db.isInvalidDate(h,s,l,d)?e?e.end=h:e={start:h,end:h}:e&&(E.push(e),e=null),h=h.add(1,"d");W.append("g").selectAll("rect").data(E).enter().append("rect").attr("id",w=>i+"-exclude-"+w.start.format("YYYY-MM-DD")).attr("x",w=>_(w.start.startOf("day"))+x).attr("y",n.gridLineStartPadding).attr("width",w=>_(w.end.endOf("day"))-_(w.start.startOf("day"))).attr("height",k-T-n.gridLineStartPadding).attr("transform-origin",function(w,b){return(_(w.start)+x+.5*(_(w.end)-_(w.start))).toString()+"px "+(b*m+.5*k).toString()+"px"}).attr("class","exclude-range")}c(it,"drawExcludeDays");function H(m,T,x,p){if(x<=0||m>T)return 1/0;const k=T-m,o=A.duration({[p??"day"]:x}).asMilliseconds();return o<=0?1/0:Math.ceil(k/o)}c(H,"getEstimatedTickCount");function at(m,T,x,p){const k=a.db.getDateFormat(),o=a.db.getAxisFormat();let l;o?l=o:k==="D"?l="%d":l=n.axisFormat??"%Y-%m-%d";let d=ge(_).tickSize(-p+T+n.gridLineStartPadding).tickFormat(Nt(l));const y=/^([1-9]\d*)(millisecond|second|minute|hour|day|week|month)$/.exec(a.db.getTickInterval()||n.tickInterval);if(y!==null){const s=parseInt(y[1],10);if(isNaN(s)||s<=0)j.warn(`Invalid tick interval value: "${y[1]}". Skipping custom tick interval.`);else{const E=y[2],e=a.db.getWeekday()||n.weekday,h=_.domain(),C=h[0],w=h[1],b=H(C,w,s,E);if(b>bt)j.warn(`The tick interval "${s}${E}" would generate ${b} ticks, which exceeds the maximum allowed (${bt}). This may indicate an invalid date or time range. Skipping custom tick interval.`);else switch(E){case"millisecond":d.ticks(Ut.every(s));break;case"second":d.ticks(Xt.every(s));break;case"minute":d.ticks(qt.every(s));break;case"hour":d.ticks(zt.every(s));break;case"day":d.ticks(Bt.every(s));break;case"week":d.ticks(Ht[e].every(s));break;case"month":d.ticks(Yt.every(s));break}}}if(W.append("g").attr("class","grid").attr("transform","translate("+m+", "+(p-50)+")").call(d).selectAll("text").style("text-anchor","middle").attr("fill","#000").attr("stroke","none").attr("font-size",10).attr("dy","1em"),a.db.topAxisEnabled()||n.topAxis){let s=Ce(_).tickSize(-p+T+n.gridLineStartPadding).tickFormat(Nt(l));if(y!==null){const E=parseInt(y[1],10);if(isNaN(E)||E<=0)j.warn(`Invalid tick interval value: "${y[1]}". Skipping custom tick interval.`);else{const e=y[2],h=a.db.getWeekday()||n.weekday,C=_.domain(),w=C[0],b=C[1];if(H(w,b,E,e)<=bt)switch(e){case"millisecond":s.ticks(Ut.every(E));break;case"second":s.ticks(Xt.every(E));break;case"minute":s.ticks(qt.every(E));break;case"hour":s.ticks(zt.every(E));break;case"day":s.ticks(Bt.every(E));break;case"week":s.ticks(Ht[h].every(E));break;case"month":s.ticks(Yt.every(E));break}}}W.append("g").attr("class","grid").attr("transform","translate("+m+", "+T+")").call(s).selectAll("text").style("text-anchor","middle").attr("fill","#000").attr("stroke","none").attr("font-size",10)}}c(at,"makeGrid");function rt(m,T){let x=0;const p=Object.keys(B).map(k=>[k,B[k]]);W.append("g").selectAll("text").data(p).enter().append(function(k){const o=k[0].split(De.lineBreakRegex),l=-(o.length-1)/2,d=L.createElementNS("http://www.w3.org/2000/svg","text");d.setAttribute("dy",l+"em");for(const[u,y]of o.entries()){const s=L.createElementNS("http://www.w3.org/2000/svg","tspan");s.setAttribute("alignment-baseline","central"),s.setAttribute("x","10"),u>0&&s.setAttribute("dy","1em"),s.textContent=y,d.appendChild(s)}return d}).attr("x",10).attr("y",function(k,o){if(o>0)for(let l=0;l<o;l++)return x+=p[o-1][1],k[1]*m/2+x*m+T;else return k[1]*m/2+T}).attr("font-size",n.sectionFontSize).attr("class",function(k){for(const[o,l]of M.entries())if(k[0]===l)return"sectionTitle sectionTitle"+o%n.numberSectionStyles;return"sectionTitle"})}c(rt,"vertLabels");function nt(m,T,x,p){const k=a.db.getTodayMarker();if(k==="off")return;const o=W.append("g").attr("class","today"),l=new Date,d=o.append("line");d.attr("x1",_(l)+m).attr("x2",_(l)+m).attr("y1",n.titleTopMargin).attr("y2",p-n.titleTopMargin).attr("class","today"),k!==""&&d.attr("style",k.replace(/,/g,";"))}c(nt,"drawToday");function ct(m){const T={},x=[];for(let p=0,k=m.length;p<k;++p)Object.prototype.hasOwnProperty.call(T,m[p])||(T[m[p]]=!0,x.push(m[p]));return x}c(ct,"checkUnique")},"draw"),xs={setConf:ps,draw:Ts},bs=c(t=>`
  .mermaid-main-font {
        font-family: ${t.fontFamily};
  }

  .exclude-range {
    fill: ${t.excludeBkgColor};
  }

  .section {
    stroke: none;
    opacity: 0.2;
  }

  .section0 {
    fill: ${t.sectionBkgColor};
  }

  .section2 {
    fill: ${t.sectionBkgColor2};
  }

  .section1,
  .section3 {
    fill: ${t.altSectionBkgColor};
    opacity: 0.2;
  }

  .sectionTitle0 {
    fill: ${t.titleColor};
  }

  .sectionTitle1 {
    fill: ${t.titleColor};
  }

  .sectionTitle2 {
    fill: ${t.titleColor};
  }

  .sectionTitle3 {
    fill: ${t.titleColor};
  }

  .sectionTitle {
    text-anchor: start;
    font-family: ${t.fontFamily};
  }


  /* Grid and axis */

  .grid .tick {
    stroke: ${t.gridColor};
    opacity: 0.8;
    shape-rendering: crispEdges;
  }

  .grid .tick text {
    font-family: ${t.fontFamily};
    fill: ${t.textColor};
  }

  .grid path {
    stroke-width: 0;
  }


  /* Today line */

  .today {
    fill: none;
    stroke: ${t.todayLineColor};
    stroke-width: 2px;
  }


  /* Task styling */

  /* Default task */

  .task {
    stroke-width: 2;
  }

  .taskText {
    text-anchor: middle;
    font-family: ${t.fontFamily};
  }

  .taskTextOutsideRight {
    fill: ${t.taskTextDarkColor};
    text-anchor: start;
    font-family: ${t.fontFamily};
  }

  .taskTextOutsideLeft {
    fill: ${t.taskTextDarkColor};
    text-anchor: end;
  }


  /* Special case clickable */

  .task.clickable {
    cursor: pointer;
  }

  .taskText.clickable {
    cursor: pointer;
    fill: ${t.taskTextClickableColor} !important;
    font-weight: bold;
  }

  .taskTextOutsideLeft.clickable {
    cursor: pointer;
    fill: ${t.taskTextClickableColor} !important;
    font-weight: bold;
  }

  .taskTextOutsideRight.clickable {
    cursor: pointer;
    fill: ${t.taskTextClickableColor} !important;
    font-weight: bold;
  }


  /* Specific task settings for the sections*/

  .taskText0,
  .taskText1,
  .taskText2,
  .taskText3 {
    fill: ${t.taskTextColor};
  }

  .task0,
  .task1,
  .task2,
  .task3 {
    fill: ${t.taskBkgColor};
    stroke: ${t.taskBorderColor};
  }

  .taskTextOutside0,
  .taskTextOutside2
  {
    fill: ${t.taskTextOutsideColor};
  }

  .taskTextOutside1,
  .taskTextOutside3 {
    fill: ${t.taskTextOutsideColor};
  }


  /* Active task */

  .active0,
  .active1,
  .active2,
  .active3 {
    fill: ${t.activeTaskBkgColor};
    stroke: ${t.activeTaskBorderColor};
  }

  .activeText0,
  .activeText1,
  .activeText2,
  .activeText3 {
    fill: ${t.taskTextDarkColor} !important;
  }


  /* Completed task */

  .done0,
  .done1,
  .done2,
  .done3 {
    stroke: ${t.doneTaskBorderColor};
    fill: ${t.doneTaskBkgColor};
    stroke-width: 2;
  }

  .doneText0,
  .doneText1,
  .doneText2,
  .doneText3 {
    fill: ${t.taskTextDarkColor} !important;
  }

  /* Done task text displayed outside the bar sits against the diagram background,
     not against the done-task bar, so it must use the outside/contrast color. */
  .doneText0.taskTextOutsideLeft,
  .doneText0.taskTextOutsideRight,
  .doneText1.taskTextOutsideLeft,
  .doneText1.taskTextOutsideRight,
  .doneText2.taskTextOutsideLeft,
  .doneText2.taskTextOutsideRight,
  .doneText3.taskTextOutsideLeft,
  .doneText3.taskTextOutsideRight {
    fill: ${t.taskTextOutsideColor} !important;
  }


  /* Tasks on the critical line */

  .crit0,
  .crit1,
  .crit2,
  .crit3 {
    stroke: ${t.critBorderColor};
    fill: ${t.critBkgColor};
    stroke-width: 2;
  }

  .activeCrit0,
  .activeCrit1,
  .activeCrit2,
  .activeCrit3 {
    stroke: ${t.critBorderColor};
    fill: ${t.activeTaskBkgColor};
    stroke-width: 2;
  }

  .doneCrit0,
  .doneCrit1,
  .doneCrit2,
  .doneCrit3 {
    stroke: ${t.critBorderColor};
    fill: ${t.doneTaskBkgColor};
    stroke-width: 2;
    cursor: pointer;
    shape-rendering: crispEdges;
  }

  .milestone {
    transform: rotate(45deg) scale(0.8,0.8);
  }

  .milestoneText {
    font-style: italic;
  }
  .doneCritText0,
  .doneCritText1,
  .doneCritText2,
  .doneCritText3 {
    fill: ${t.taskTextDarkColor} !important;
  }

  /* Done-crit task text outside the bar — same reasoning as doneText above. */
  .doneCritText0.taskTextOutsideLeft,
  .doneCritText0.taskTextOutsideRight,
  .doneCritText1.taskTextOutsideLeft,
  .doneCritText1.taskTextOutsideRight,
  .doneCritText2.taskTextOutsideLeft,
  .doneCritText2.taskTextOutsideRight,
  .doneCritText3.taskTextOutsideLeft,
  .doneCritText3.taskTextOutsideRight {
    fill: ${t.taskTextOutsideColor} !important;
  }

  .vert {
    stroke: ${t.vertLineColor};
  }

  .vertText {
    font-size: 15px;
    text-anchor: middle;
    fill: ${t.vertLineColor} !important;
  }

  .activeCritText0,
  .activeCritText1,
  .activeCritText2,
  .activeCritText3 {
    fill: ${t.taskTextDarkColor} !important;
  }

  .titleText {
    text-anchor: middle;
    font-size: 18px;
    fill: ${t.titleColor||t.textColor};
    font-family: ${t.fontFamily};
  }
`,"getStyles"),ws=bs,Es={parser:Oe,db:gs,renderer:xs,styles:ws};export{Es as diagram};
