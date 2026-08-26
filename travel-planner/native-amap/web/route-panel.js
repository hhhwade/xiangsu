(function () {
  var colors = ['#DE7444','#5E9C93','#7A71B8','#C58C45','#4B86A4','#A66573'];
  var preferenceNames = ['自然风光','历史人文','美食探店','博物馆','宗教寺庙','网红打卡','购物商圈','户外运动'];
  var modeNames = ['步行','骑行','自驾','公交'];
  var modeKey = { '步行':'walking', '骑行':'riding', '自驾':'driving', '公交':'transit' };
  var modeProfiles = {
    walking:{speed:4.5,road:1.10,wait:0,label:'步行',suffix:'慢游步行线'},
    riding:{speed:12,road:1.16,wait:2,label:'骑行',suffix:'轻松骑行线'},
    driving:{speed:27,road:1.30,wait:5,label:'自驾',suffix:'高效自驾线'},
    transit:{speed:18,road:1.24,wait:10,label:'公交',suffix:'公共交通线'}
  };
  var selectedPrefs = ['自然风光','历史人文','美食探店','博物馆'];
  var selectedMode = 'driving';
  var activeDay = 1;
  var selectedId = '';
  var dragIndex = null;
  var routes = [];

  /* National city centre cache. Inputs outside this cache still work in offline
     demonstration mode with a deterministic China-region fallback; production API
     uses AMap POI/geocoding to replace the fallback with real POIs. */
  var cityCenters = {
    '北京':[116.4074,39.9042],'上海':[121.4737,31.2304],'天津':[117.2000,39.1333],'重庆':[106.5516,29.5630],
    '石家庄':[114.5149,38.0428],'唐山':[118.1802,39.6305],'秦皇岛':[119.6005,39.9354],'保定':[115.4646,38.8744],'邯郸':[114.5391,36.6256],'张家口':[114.8859,40.7689],'承德':[117.9624,40.9541],
    '太原':[112.5489,37.8706],'大同':[113.3001,40.0768],'长治':[113.1165,36.1954],'临汾':[111.5189,36.0881],'运城':[111.0071,35.0264],
    '呼和浩特':[111.7492,40.8426],'包头':[109.8403,40.6574],'鄂尔多斯':[109.7813,39.6083],'赤峰':[118.8892,42.2640],
    '沈阳':[123.4315,41.8057],'大连':[121.6147,38.9140],'鞍山':[122.9956,41.1106],'丹东':[124.3547,40.0005],'锦州':[121.1269,41.0951],
    '长春':[125.3235,43.8171],'吉林':[126.5496,43.8379],'延边':[129.5091,42.9048],
    '哈尔滨':[126.5349,45.8038],'齐齐哈尔':[123.9182,47.3543],'牡丹江':[129.6332,44.5515],'佳木斯':[130.3189,46.8000],'大庆':[125.1038,46.5895],
    '南京':[118.7969,32.0603],'无锡':[120.3119,31.4912],'徐州':[117.2841,34.2058],'常州':[119.9741,31.8112],'苏州':[120.5853,31.2989],'南通':[120.8646,32.0162],'扬州':[119.4127,32.3942],'镇江':[119.4250,32.1878],
    '杭州':[120.1551,30.2741],'宁波':[121.5503,29.8746],'温州':[120.6994,27.9949],'嘉兴':[120.7555,30.7461],'湖州':[120.0868,30.8943],'绍兴':[120.5821,29.9971],'金华':[119.6474,29.0792],'舟山':[122.2072,29.9853],'台州':[121.4208,28.6564],'丽水':[119.9232,28.4676],
    '合肥':[117.2272,31.8206],'芜湖':[118.4329,31.3529],'黄山':[118.3387,29.7147],'阜阳':[115.8143,32.8901],'安庆':[117.1153,30.5319],
    '福州':[119.2965,26.0745],'厦门':[118.0894,24.4798],'泉州':[118.6757,24.8744],'漳州':[117.6475,24.5130],'莆田':[119.0078,25.4541],'龙岩':[117.0174,25.0750],
    '南昌':[115.8582,28.6829],'九江':[115.9536,29.6612],'赣州':[114.9359,25.8453],'上饶':[117.9431,28.4549],
    '济南':[117.1201,36.6512],'青岛':[120.3826,36.0671],'烟台':[121.4479,37.4638],'威海':[122.1205,37.5131],'潍坊':[119.1617,36.7069],'临沂':[118.3564,35.1047],'泰安':[117.0884,36.2003],
    '郑州':[113.6254,34.7466],'洛阳':[112.4540,34.6197],'开封':[114.3076,34.7973],'南阳':[112.5283,32.9909],'安阳':[114.3924,36.0976],'新乡':[113.9268,35.3030],
    '武汉':[114.3054,30.5931],'宜昌':[111.2865,30.6919],'襄阳':[112.1224,32.0089],'荆州':[112.2419,30.3350],'黄冈':[114.8724,30.4537],
    '长沙':[112.9388,28.2282],'张家界':[110.4792,29.1171],'岳阳':[113.1290,29.3571],'衡阳':[112.5719,26.8932],'湘潭':[112.9441,27.8297],
    '广州':[113.2644,23.1291],'深圳':[114.0579,22.5431],'珠海':[113.5767,22.2707],'佛山':[113.1214,23.0215],'东莞':[113.7518,23.0207],'中山':[113.3926,22.5176],'汕头':[116.6819,23.3542],'惠州':[114.4168,23.1115],'湛江':[110.3594,21.2707],'江门':[113.0815,22.5787],
    '南宁':[108.3665,22.8170],'桂林':[110.2900,25.2736],'北海':[109.1193,21.4733],'柳州':[109.4281,24.3264],
    '海口':[110.1983,20.0440],'三亚':[109.5119,18.2528],
    '成都':[104.0665,30.5728],'绵阳':[104.6796,31.4675],'乐山':[103.7654,29.5522],'宜宾':[104.6437,28.7513],'南充':[106.1107,30.8378],'泸州':[105.4433,28.8891],
    '贵阳':[106.6302,26.6470],'遵义':[106.9274,27.7257],'安顺':[105.9476,26.2531],'毕节':[105.2850,27.3017],
    '昆明':[102.8329,24.8801],'大理':[100.2676,25.6065],'丽江':[100.2278,26.8550],'西双版纳':[100.7970,22.0017],'曲靖':[103.7979,25.5016],
    '拉萨':[91.1409,29.6456],'日喀则':[88.8806,29.2669],'林芝':[94.3615,29.6489],
    '西安':[108.9398,34.3416],'宝鸡':[107.2377,34.3619],'咸阳':[108.7089,34.3296],'延安':[109.4897,36.5853],'汉中':[107.0238,33.0676],
    '兰州':[103.8343,36.0611],'嘉峪关':[98.2891,39.7731],'天水':[105.7249,34.5809],'张掖':[100.4498,38.9259],
    '西宁':[101.7782,36.6171],'银川':[106.2309,38.4872],'乌鲁木齐':[87.6168,43.8256],'喀什':[75.9898,39.4704],'伊宁':[81.3241,43.9168],'克拉玛依':[84.8739,45.5959],
    '香港':[114.1694,22.3193],'澳门':[113.5439,22.1987],'台北':[121.5654,25.0330],'高雄':[120.3014,22.6273]
  };

  var cityCatalogs = {
    '杭州':[
      ['断桥残雪','自然风光',120.1500,30.2600,45],['白堤','自然风光',120.1433,30.2509,60],['平湖秋月','网红打卡',120.1367,30.2482,40],['楼外楼','美食探店',120.1304,30.2382,75],['曲院风荷','自然风光',120.1248,30.2316,75],['苏堤春晓','自然风光',120.1192,30.2216,60],['灵隐寺','宗教寺庙',120.1013,30.2338,90],['飞来峰','历史人文',120.1001,30.2303,75],['龙井村','户外运动',120.0952,30.1882,100],['中国茶叶博物馆','博物馆',120.1060,30.1941,80],['拱宸桥','历史人文',120.1498,30.3133,45],['京杭大运河博物馆','博物馆',120.1509,30.3090,100]
    ],
    '北京':[
      ['天安门广场','历史人文',116.3975,39.9087,50],['故宫博物院','博物馆',116.3970,39.9180,180],['景山公园','自然风光',116.3976,39.9241,65],['北海公园','自然风光',116.3836,39.9249,100],['什刹海','历史人文',116.3855,39.9415,95],['南锣鼓巷','美食探店',116.4038,39.9372,80],['天坛公园','历史人文',116.4074,39.8822,130],['798艺术区','网红打卡',116.4948,39.9840,120],['颐和园','自然风光',116.2740,39.9997,180]
    ],
    '上海':[
      ['外滩','网红打卡',121.4900,31.2410,70],['南京路步行街','购物商圈',121.4755,31.2387,90],['豫园','历史人文',121.4928,31.2273,100],['上海博物馆','博物馆',121.4754,31.2302,140],['新天地','美食探店',121.4758,31.2191,100],['武康路','网红打卡',121.4402,31.2032,75],['西岸艺术中心','博物馆',121.4535,31.1778,110],['陆家嘴滨江','自然风光',121.5090,31.2405,80]
    ],
    '广州':[
      ['陈家祠','历史人文',113.2444,23.1257,90],['永庆坊','网红打卡',113.2316,23.1135,75],['沙面','历史人文',113.2372,23.1076,70],['北京路步行街','购物商圈',113.2691,23.1222,90],['广州塔','网红打卡',113.3306,23.1136,90],['珠江夜游码头','自然风光',113.3176,23.1081,80],['广东省博物馆','博物馆',113.3210,23.1173,120],['上下九步行街','美食探店',113.2446,23.1151,90]
    ],
    '深圳':[
      ['莲花山公园','自然风光',114.0604,22.5543,90],['市民中心','网红打卡',114.0583,22.5443,45],['深圳博物馆','博物馆',114.0670,22.5471,100],['华强北','购物商圈',114.0857,22.5475,90],['欢乐海岸','美食探店',113.9962,22.5331,100],['海上世界','网红打卡',113.9100,22.4847,90],['大梅沙海滨公园','自然风光',114.3072,22.6032,120]
    ],
    '成都':[
      ['宽窄巷子','历史人文',104.0496,30.6740,100],['人民公园','自然风光',104.0564,30.6609,75],['武侯祠','历史人文',104.0430,30.6456,100],['锦里','美食探店',104.0422,30.6437,90],['杜甫草堂','博物馆',104.0297,30.6611,120],['春熙路','购物商圈',104.0830,30.6570,100],['大熊猫繁育研究基地','亲子乐园',104.1481,30.7337,180]
    ],
    '西安':[
      ['钟楼','历史人文',108.9480,34.2601,45],['回民街','美食探店',108.9468,34.2647,90],['西安城墙','历史人文',108.9485,34.2552,110],['碑林博物馆','博物馆',108.9558,34.2444,90],['大雁塔','历史人文',108.9642,34.2186,100],['大唐不夜城','网红打卡',108.9689,34.2161,90],['陕西历史博物馆','博物馆',108.9650,34.2309,140]
    ],
    '重庆':[
      ['解放碑','购物商圈',106.5750,29.5550,80],['洪崖洞','网红打卡',106.5817,29.5637,90],['长江索道','网红打卡',106.5838,29.5576,70],['磁器口古镇','历史人文',106.4550,29.5835,110],['三峡博物馆','博物馆',106.5504,29.5644,120],['南山一棵树','自然风光',106.6040,29.5320,80]
    ],
    '厦门':[
      ['鼓浪屿','自然风光',118.0708,24.4483,180],['中山路步行街','美食探店',118.0839,24.4560,90],['南普陀寺','宗教寺庙',118.0964,24.4402,80],['厦门大学外景','历史人文',118.1017,24.4375,60],['环岛路','自然风光',118.1160,24.4337,100],['沙坡尾','网红打卡',118.0910,24.4440,75]
    ],
    '南京':[
      ['中山陵','历史人文',118.8484,32.0617,140],['明孝陵','历史人文',118.8428,32.0608,110],['南京博物院','博物馆',118.8166,32.0470,130],['夫子庙','美食探店',118.7884,32.0219,100],['老门东','网红打卡',118.7910,32.0175,80],['玄武湖','自然风光',118.7967,32.0752,100]
    ],
    '苏州':[
      ['拙政园','历史人文',120.6257,31.3262,120],['苏州博物馆','博物馆',120.6275,31.3272,120],['狮子林','历史人文',120.6266,31.3294,80],['平江路','美食探店',120.6320,31.3180,100],['山塘街','网红打卡',120.6104,31.3268,90],['金鸡湖','自然风光',120.7203,31.3199,120]
    ],
    '昆明':[
      ['翠湖公园','自然风光',102.7021,25.0548,80],['云南陆军讲武堂','历史人文',102.7014,25.0559,70],['昆明老街','美食探店',102.7084,25.0404,90],['云南省博物馆','博物馆',102.7617,24.9630,120],['滇池海埂公园','自然风光',102.6545,24.9621,120]
    ],
    '三亚':[
      ['亚龙湾','自然风光',109.6339,18.2243,150],['天涯海角','自然风光',109.3570,18.2990,120],['鹿回头风景区','网红打卡',109.5200,18.2247,90],['第一市场','美食探店',109.5095,18.2474,90],['三亚千古情','主题乐园',109.5471,18.2757,150]
    ]
  };

  function $(id) { return document.getElementById(id); }
  function normalizeCity(value) { return (value || '').replace(/[\s]/g,'').replace(/市$/,'').replace(/地区$/,'').replace(/特别行政区$/,''); }
  function hash(value) { var h=2166136261; for(var i=0;i<value.length;i++){h^=value.charCodeAt(i);h+=(h<<1)+(h<<4)+(h<<7)+(h<<8)+(h<<24);} return h>>>0; }
  function fallbackCenter(city) { var h=hash(city); return [80+(h%4700)/100,20+((h/97|0)%2700)/100]; }
  function getCenter(city) { return cityCenters[normalizeCity(city)] || fallbackCenter(city); }
  function route() { for(var i=0;i<routes.length;i++)if(routes[i].day===activeDay)return routes[i]; return routes[0]; }
  function formatTime(total) { total=Math.max(0,total); return ('0'+Math.floor(total/60)).slice(-2)+':'+('0'+(total%60)).slice(-2); }
  function haversine(a,b) { var r=6371,rad=Math.PI/180,dl=(b.lat-a.lat)*rad,dn=(b.lng-a.lng)*rad;var x=Math.sin(dl/2)*Math.sin(dl/2)+Math.cos(a.lat*rad)*Math.cos(b.lat*rad)*Math.sin(dn/2)*Math.sin(dn/2);return 2*r*Math.atan2(Math.sqrt(x),Math.sqrt(1-x)); }
  function notify(text) { var t=$('toast');t.textContent='✓ '+text;t.className='toast show';clearTimeout(notify.timer);notify.timer=setTimeout(function(){t.className='toast';},2400); }
  function chosenTypes() { return selectedPrefs.length ? selectedPrefs.slice() : ['城市漫游']; }
  function genericPool(city, center, count) {
    var themes=['城市文化地标','本地风味街区','城市博物馆','公园慢游点','人文打卡点','夜景观景点','购物休闲区','城市步行街'];
    var types=chosenTypes(), result=[], i;
    for(i=0;i<count;i++) {
      var ring=Math.floor(i/6)+1, angle=(i*137.5+17)*Math.PI/180, radius=0.010*ring+0.002*(i%3);
      var lng=center[0]+Math.cos(angle)*radius/Math.max(.45,Math.cos(center[1]*Math.PI/180));
      var lat=center[1]+Math.sin(angle)*radius;
      result.push({id:'generic-'+i,name:city+themes[i%themes.length],type:types[i%types.length],lng:lng,lat:lat,duration:50+(i%4)*15,tip:'已按城市区域自动分组，可在右侧高德地图查看位置。'});
    }
    return result;
  }
  function makePool(city, days, spotsPerDay) {
    var center=getCenter(city), source=cityCatalogs[normalizeCity(city)], pool=[], i;
    if(source) {
      for(i=0;i<source.length;i++) pool.push({id:'seed-'+i,name:source[i][0],type:source[i][1],lng:source[i][2],lat:source[i][3],duration:source[i][4],tip:'建议结合右侧高德地图安排到达时间。'});
    }
    var required=Math.max(days*spotsPerDay,pool.length);
    if(pool.length<required) {
      var generic=genericPool(city,center,required-pool.length);
      for(i=0;i<generic.length;i++) pool.push(generic[i]);
    }
    return pool;
  }
  function distanceForMode(a,b,profile) { return haversine(a,b)*profile.road; }
  function orderForMode(items, mode, day) {
    var result=items.slice();
    if(mode==='walking') {
      var ordered=[result.shift()];
      while(result.length) { var current=ordered[ordered.length-1], best=0, bestD=Infinity; for(var i=0;i<result.length;i++){var d=haversine(current,result[i]);if(d<bestD){bestD=d;best=i;}} ordered.push(result.splice(best,1)[0]); }
      return ordered;
    }
    if(mode==='riding') return result.sort(function(a,b){return (day%2?a.lat-b.lat:b.lat-a.lat)||(a.lng-b.lng);});
    if(mode==='driving') return result.sort(function(a,b){return (day%2?a.lng-b.lng:b.lng-a.lng)||(a.lat-b.lat);});
    return result.sort(function(a,b){return (day%2?a.lng+a.lat-b.lng-b.lat:b.lng-a.lat-a.lng+b.lat);});
  }
  function assignSchedule(items, mode, dayHours) {
    var p=modeProfiles[mode], current=9*60, totalKm=0,totalTravel=0, i;
    for(i=0;i<items.length;i++) {
      var s=items[i];
      if(i>0) {
        var km=distanceForMode(items[i-1],s,p), minutes=Math.max(4,Math.round(km/p.speed*60+p.wait));
        current+=minutes+15; totalKm+=km; totalTravel+=minutes;
        items[i-1].next=km.toFixed(1)+' km · '+p.label+' '+minutes+' 分钟';
      }
      s.arrive=formatTime(current); current+=s.duration; s.leave=formatTime(current);
    }
    return {km:totalKm,travel:totalTravel,end:current};
  }
  function buildRoutes(city, dayCount, dailyHours, mode) {
    var spotsPerDay=dailyHours<=5?3:(dailyHours>=10?5:4), pool=makePool(city,dayCount,spotsPerDay), result=[], themes=['经典人文线','城市慢游线','风味探索线','自然轻行线','艺文打卡线','夜景漫游线'], i;
    for(i=0;i<dayCount;i++) {
      var group=pool.slice(i*spotsPerDay,(i+1)*spotsPerDay), ordered=orderForMode(group,mode,i+1), schedule=assignSchedule(ordered,mode,dailyHours), profile=modeProfiles[mode];
      result.push({day:i+1,title:city+themes[i%themes.length],color:colors[i%colors.length],summary:'Day '+(i+1)+' 围绕同一区域安排，按 '+profile.label+' 重新优化游览顺序，减少折返。',distance:schedule.km.toFixed(1)+' km',visit:(ordered.reduce(function(n,s){return n+s.duration;},0)/60).toFixed(1)+' h',transport:(schedule.travel/60).toFixed(1)+' h',notice:'每段已预留 15 分钟缓冲；右侧高德地图显示当前 '+profile.label+' 顺序。',transportMode:mode,spots:ordered});
    }
    return result;
  }
  function publish() {
    var r=route(); if(!r)return;
    var data={transportMode:r.transportMode,routes:[{day:r.day,title:r.title,color:r.color,spots:r.spots.map(function(s){return {name:s.name,arrivalTime:s.arrive,location:{lng:s.lng,lat:s.lat}};})}]};
    try { if(window.XingjiNativeMap && window.XingjiNativeMap.updateRoute) window.XingjiNativeMap.updateRoute(JSON.stringify(data)); } catch(e) {}
  }
  function focus(s) { selectedId=s.id;renderRoute();try{if(window.XingjiNativeMap&&window.XingjiNativeMap.focusSpot)window.XingjiNativeMap.focusSpot(s.lat,s.lng);}catch(e){} }
  function renderPrefs() { $('prefs').innerHTML=preferenceNames.map(function(p){return '<button class="chip '+(selectedPrefs.indexOf(p)>=0?'on':'')+'" data-pref="'+p+'">'+p+'</button>';}).join('');var list=document.querySelectorAll('[data-pref]');for(var i=0;i<list.length;i++)list[i].onclick=function(){var p=this.getAttribute('data-pref'),at=selectedPrefs.indexOf(p);if(at>=0)selectedPrefs.splice(at,1);else selectedPrefs.push(p);renderPrefs();}; }
  function renderModes() { $('modes').innerHTML=modeNames.map(function(m){return '<button class="mode '+(modeKey[m]===selectedMode?'on':'')+'" data-mode="'+modeKey[m]+'">'+m+'</button>';}).join('');var list=document.querySelectorAll('[data-mode]');for(var i=0;i<list.length;i++)list[i].onclick=function(){selectedMode=this.getAttribute('data-mode');generatePlan(false);notify('已按 '+modeProfiles[selectedMode].label+' 重新计算路线与交通时间');}; }
  function renderDays() { $('days').innerHTML=routes.map(function(r){return '<button class="day '+(r.day===activeDay?'on':'')+'" data-day="'+r.day+'"><i class="day-dot" style="background:'+r.color+'"></i>Day '+r.day+'</button>';}).join('');var list=document.querySelectorAll('[data-day]');for(var i=0;i<list.length;i++)list[i].onclick=function(){activeDay=Number(this.getAttribute('data-day'));selectedId='';renderAll();}; }
  function esc(s){return String(s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
  function renderRoute() {
    var r=route(); if(!r)return; var profile=modeProfiles[r.transportMode], html='';
    html+='<div class="route-title"><span class="route-bar" style="background:'+r.color+'"></span><div><p>DAY '+('0'+r.day).slice(-2)+' · '+profile.label+'优化</p><h3>'+esc(r.title)+'</h3></div></div>';
    html+='<p class="route-desc">'+esc(r.summary)+'</p><div class="stats"><span><b>'+r.spots.length+'</b> 个地点</span><i></i><span><b>'+r.distance+'</b> 路程</span><i></i><span><b>'+r.visit+'</b> 游玩</span></div>';
    html+='<div class="optimized"><span>✓</span><span>已完成 <b>区域聚类 + 2-opt</b></span><em>'+profile.label+'路线</em></div><ol class="spots">';
    r.spots.forEach(function(s,i){html+='<li class="spot '+(selectedId===s.id?'selected':'')+'" draggable="true" data-index="'+i+'"><div class="spot-time">'+s.arrive+'<i class="order" style="background:'+r.color+'">'+(i+1)+'</i></div><div class="spot-box"><div class="spot-name"><span>'+esc(s.name)+'</span><span>⌖</span></div><div class="spot-meta"><b>'+esc(s.type)+'</b> · 游览约 '+s.duration+' 分钟 · '+s.leave+' 离开</div><p class="spot-tip">'+esc(s.tip)+'</p></div>'+(s.next?'<div class="segment"><span>⌁</span>'+esc(s.next)+' · 缓冲 15 分钟</div>':'')+'</li>';});
    html+='</ol><div class="notice"><b>✦ 今日提醒</b><br>'+esc(r.notice)+'</div>';$('routeCard').innerHTML=html;
    var nodes=document.querySelectorAll('.spot');for(var j=0;j<nodes.length;j++){nodes[j].onclick=(function(index){return function(){focus(r.spots[index]);};})(j);nodes[j].ondragstart=(function(index){return function(){dragIndex=index;};})(j);nodes[j].ondragover=function(e){e.preventDefault();};nodes[j].ondrop=(function(index){return function(e){e.preventDefault();if(dragIndex===null||dragIndex===index)return;var moved=r.spots.splice(dragIndex,1)[0];r.spots.splice(index,0,moved);dragIndex=null;selectedId=moved.id;renderRoute();publish();notify('景点顺序已调整，右侧高德地图已重绘');};})(j);}
  }
  function renderAll() { var city=$('destination').value.trim()||'杭州';$('itineraryTitle').textContent=city+' · '+routes.length+' 天路线';renderDays();renderRoute();publish(); }
  function generatePlan(showNotice) { var city=$('destination').value.trim()||'杭州',days=Math.max(1,Math.min(30,parseInt($('duration').value,10)||1)),hours=Math.max(2,Math.min(16,parseInt($('hours').value,10)||8));$('duration').value=days;$('hours').value=hours;routes=buildRoutes(city,days,hours,selectedMode);activeDay=1;selectedId='';renderModes();renderAll();if(!cityCenters[normalizeCity(city)]&&!cityCatalogs[normalizeCity(city)])notify('已启用 '+city+' 全国城市离线扩展路线；部署 API 后会补充实时 POI');else if(showNotice)notify('已为 '+city+' 生成 '+days+' 天 '+modeProfiles[selectedMode].label+' 路线'); }
  function initCityList() { var names=[];for(var n in cityCenters)if(cityCenters.hasOwnProperty(n))names.push(n);names.sort();$('cityList').innerHTML=names.map(function(n){return '<option value="'+esc(n)+'"></option>';}).join(''); }
  $('generate').onclick=function(){generatePlan(true);};
  initCityList();renderPrefs();renderModes();generatePlan(false);
})();
