// macOS Vision helper for the pinned 570x410 Flash layout in a 600x450 screenshot.
// Reads image pixels only. Synthetic numeric context aids OCR; its prefix is
// removed before returning values. Unknown numbers remain absent. Hero and
// modal candidates are heuristics, never automatic game-completion evidence.
import Foundation
import Vision
import CoreGraphics
import ImageIO
import CoreText

func readText(_ img:CGImage)->[[String:Any]] {
 let req=VNRecognizeTextRequest();req.recognitionLevel = .accurate;req.usesLanguageCorrection=false;req.recognitionLanguages=["en-US","zh-Hans"];req.minimumTextHeight=0.005
 let temp=URL(fileURLWithPath:"generated/visible-hud-ocrinput-\(ProcessInfo.processInfo.processIdentifier).png")
 defer {try? FileManager.default.removeItem(at:temp)}
 guard let dest=CGImageDestinationCreateWithURL(temp as CFURL,"public.png" as CFString,1,nil) else{return []}
 CGImageDestinationAddImage(dest,img,nil)
 guard CGImageDestinationFinalize(dest) else{return []}
 do {try VNImageRequestHandler(url:temp,options:[:]).perform([req])}catch{return []}
 return (req.results ?? []).compactMap{x in guard let t=x.topCandidates(1).first else{return nil};return ["text":t.string,"confidence":t.confidence,"x":Double(x.boundingBox.midX),"y":Double(x.boundingBox.midY)]}
}
func inspect(_ filename:String,withHUD:Bool=true,withSceneText:Bool=false)->[String:Any] {
 let started=Date();guard let src=CGImageSourceCreateWithURL(URL(fileURLWithPath:filename) as CFURL,nil),let img=CGImageSourceCreateImageAtIndex(src,0,nil)else{return ["error":"Unable to load image"]}
 guard img.width>=570 && img.height>=410 else{return ["error":"Screenshot is smaller than the fixed layout"]}
 let fields:[(String,CGRect)]=[("hp",CGRect(x:80,y:84,width:70,height:24)),("atk",CGRect(x:80,y:108,width:70,height:24)),("def",CGRect(x:80,y:132,width:70,height:24)),("money",CGRect(x:80,y:156,width:70,height:24)),("experience",CGRect(x:80,y:180,width:70,height:24)),("yellow",CGRect(x:80,y:214,width:50,height:27)),("blue",CGRect(x:80,y:246,width:50,height:27)),("red",CGRect(x:80,y:278,width:50,height:27)),("level",CGRect(x:88,y:41,width:42,height:33))]
 let w=img.width,h=img.height;var bytes=[UInt8](repeating:0,count:w*h*4)
 let ctx=CGContext(data:&bytes,width:w,height:h,bitsPerComponent:8,bytesPerRow:w*4,space:CGColorSpaceCreateDeviceRGB(),bitmapInfo:CGImageAlphaInfo.premultipliedLast.rawValue|CGBitmapInfo.byteOrder32Big.rawValue)!
 ctx.draw(img,in:CGRect(x:0,y:0,width:w,height:h))
 var values:[String:Any]=[:],raw:[String:Any]=[:]
 var directValues:[String:Any]=[:]
 var directReadings:[String:[Int]]=[:]
 var directCandidates:[String:[[String:Any]]]=[:]
 var contextualKeyCandidates:[String:Int]=[:]
 if withHUD {
 let rowHeight=180,canvasHeight=fields.count*180
 let composite=CGContext(data:nil,width:800,height:canvasHeight,bitsPerComponent:8,bytesPerRow:0,space:CGColorSpaceCreateDeviceRGB(),bitmapInfo:CGImageAlphaInfo.premultipliedLast.rawValue)!
 composite.setFillColor(CGColor(gray:0.22,alpha:1));composite.fill(CGRect(x:0,y:0,width:800,height:canvasHeight));composite.interpolationQuality = .none
 for (i,entry) in fields.enumerated(){
  // Remove the stone texture and colored UI borders, retaining only actual
  // light neutral foreground pixels in the numeric region. No digits are added.
  let cw=Int(entry.1.width),ch=Int(entry.1.height);var glyph=[UInt8](repeating:255,count:cw*ch*4)
  for gy in 0..<ch{for gx in 0..<cw{
   let source=((Int(entry.1.minY)+gy)*w+Int(entry.1.minX)+gx)*4
   let low=min(bytes[source],min(bytes[source+1],bytes[source+2])),high=max(bytes[source],max(bytes[source+1],bytes[source+2]))
   let value:UInt8=low>180 && Int(high)-Int(low)<30 ? low:56
   let dest=(gy*cw+gx)*4;glyph[dest]=value;glyph[dest+1]=value;glyph[dest+2]=value
  }}
  let provider=CGDataProvider(data:Data(glyph) as CFData)!
  if let crop=CGImage(width:cw,height:ch,bitsPerComponent:8,bitsPerPixel:32,bytesPerRow:cw*4,space:CGColorSpaceCreateDeviceRGB(),bitmapInfo:CGBitmapInfo(rawValue:CGImageAlphaInfo.premultipliedLast.rawValue|CGBitmapInfo.byteOrder32Big.rawValue),provider:provider,decode:nil,shouldInterpolate:false,intent:.defaultIntent){composite.draw(crop,in:CGRect(x:400,y:(fields.count-1-i)*rowHeight+12,width:cw*5,height:ch*5))}
  var firstX=Int(entry.1.width),minY=Int(entry.1.height),maxY=0
  for yy in Int(entry.1.minY)..<Int(entry.1.maxY){for xx in Int(entry.1.minX)..<Int(entry.1.maxX){let at=(yy*w+xx)*4;if min(bytes[at],min(bytes[at+1],bytes[at+2]))>220{firstX=min(firstX,xx-Int(entry.1.minX));minY=min(minY,yy-Int(entry.1.minY));maxY=max(maxY,yy-Int(entry.1.minY))}}}
  let size=Double(max(12,maxY-minY+1))*5*1.35
  let text=NSAttributedString(string:"123",attributes:[NSAttributedString.Key(kCTFontAttributeName as String):CTFontCreateWithName("Arial-BoldItalicMT" as CFString,size,nil),NSAttributedString.Key(kCTForegroundColorAttributeName as String):CGColor(gray:1,alpha:1)])
  let line=CTLineCreateWithAttributedString(text),bounds=CTLineGetImageBounds(line,nil)
  let bottom=Double((fields.count-1-i)*rowHeight+12)+Double(entry.1.height-1-Double(maxY))*5
  composite.textPosition=CGPoint(x:max(2,400+Double(firstX)*5-bounds.maxX-8),y:bottom-bounds.minY);CTLineDraw(line,composite)

 }

 let compositeImage=composite.makeImage()!

 let rows=readText(compositeImage)
 for item in rows {
  guard let y=item["y"] as? Double,let t=item["text"] as? String,let confidence=item["confidence"] as? Float else{continue}
  let row=Int((1-y)*Double(fields.count));if row<0||row>=fields.count{continue};let name=fields[row].0;raw[name]=item
  let numeric=t.replacingOccurrences(of:" ",with:"").replacingOccurrences(of:"O",with:"0");let clean=numeric.hasPrefix("123") ? String(numeric.dropFirst(3)).trimmingCharacters(in:CharacterSet(charactersIn:"-_.,:")):""
  if confidence >= 0.7 && !clean.isEmpty && clean.allSatisfy({$0.isNumber}),let n=Int(clean){values[name]=n}
  if confidence >= 0.7 && ["yellow","blue","red"].contains(name) && clean.contains("Z"){
   let repaired=clean.replacingOccurrences(of:"Z",with:"2")
   if !repaired.isEmpty && repaired.allSatisfy({$0.isNumber}),let n=Int(repaired){contextualKeyCandidates[name]=n}
  }
 }


 // Independent direct-crop OCR at two sizes for the five numeric stat rows.
 // The synthetic-prefix composite can confuse similar glyphs (e.g. 113/117);
 // direct crops at both scales can share the same error (remote HP860 ->98).
 // Keep those readings as diagnostics. Only DEF has a demonstrated contextual
 // glyph error (113 ->117) corrected by agreement between both direct scales;
 // retain the contextual reading for the other fields.
 for entry in fields where ["hp","atk","def","experience"].contains(entry.0) || (["yellow","blue","red"].contains(entry.0) && values[entry.0] == nil){
  guard let crop=img.cropping(to:entry.1) else{continue}
  let scales=["yellow","blue","red"].contains(entry.0) ? [3,4,5,6,8] : [3,5]
  for scale in scales{
   guard let direct=CGContext(data:nil,width:crop.width*scale,height:crop.height*scale,bitsPerComponent:8,bytesPerRow:0,space:CGColorSpaceCreateDeviceRGB(),bitmapInfo:CGImageAlphaInfo.premultipliedLast.rawValue) else{continue}
   direct.interpolationQuality = .none
   direct.setFillColor(CGColor(gray:0.22,alpha:1));direct.fill(CGRect(x:0,y:0,width:crop.width*scale,height:crop.height*scale))
   direct.draw(crop,in:CGRect(x:0,y:0,width:crop.width*scale,height:crop.height*scale))
   let request=VNRecognizeTextRequest();request.recognitionLevel = .accurate;request.usesLanguageCorrection=false;request.recognitionLanguages=["en-US"]
   do{try VNImageRequestHandler(cgImage:direct.makeImage()!,options:[:]).perform([request])}catch{continue}
   guard let candidate=request.results?.first?.topCandidates(1).first,candidate.confidence>=0.7 else{continue}
   directCandidates[entry.0,default:[]].append(["scale":scale,"text":candidate.string,"confidence":candidate.confidence])
   let digits=String(candidate.string.filter(\.isNumber))
   if let number=Int(digits){directReadings[entry.0,default:[]].append(number);if scale==3{directValues[entry.0]=number}}
  }
 }
 for entry in fields.prefix(5) where entry.0 == "def"{
  let readings=directReadings[entry.0] ?? []
  if readings.count>=2 && readings.allSatisfy({$0==readings[0]}){
   values[entry.0]=readings[0]
  }
 }
 // A demonstrated ATK truncation (43 ->4) is corrected only when both
 // direct scales agree and the contextual value is a strict leading prefix.
 // This does not enable direct-crop overrides for HP or unrelated ATK errors.
 if let primary=values["atk"] as? Int {
  let readings=directReadings["atk"] ?? []
  if readings.count>=2 && readings.allSatisfy({$0==readings[0]}) {
   let direct=String(readings[0]), contextual=String(primary)
   if direct.count>contextual.count && direct.hasPrefix(contextual){values["atk"]=readings[0]}
  }
 }
 // A numeric key glyph can be classified as a letter (e.g. contextual123Z).
 // Fill only an absent key value when at least two scales agree, or when an
 // observed contextual Z/2 confusion is corroborated by a literal numeric
 // direct crop. All parsed direct numbers must agree; the plan is never read.
 for name in ["yellow","blue","red"] where values[name] == nil{
  let readings=directReadings[name] ?? []
  if readings.count>=2 && readings.allSatisfy({$0==readings[0]}){
   values[name]=readings[0]
  }else if let candidate=contextualKeyCandidates[name],!readings.isEmpty && readings.allSatisfy({$0==candidate}){
   values[name]=candidate
  }
 }
 }

 var orangeMaxRun=0
 for y in 45..<370 {var run=0;for x in 200..<533{let p=(y*w+x)*4;let r=Int(bytes[p]),g=Int(bytes[p+1]),b=Int(bytes[p+2]);if r>130&&g>60&&g<200&&b<130&&r-g>25&&g-b>20{run+=1;orangeMaxRun=max(orangeMaxRun,run)}else{run=0}}}
 var heroes:[[String:Int]]=[];var black=0,total=0
 for y in 0..<11 {for x in 0..<11 {
  var skin=0,blue=0,white=0
  for yy in (31+32*y)..<(63+32*y) {for xx in (191+32*x)..<(223+32*x) {
   let p=(yy*w+xx)*4;let r=Int(bytes[p]),g=Int(bytes[p+1]),b=Int(bytes[p+2]);total+=1
   if max(r,max(g,b))<8{black+=1}
   if r>210&&g>140&&g<220&&b>70&&r-b>35{skin+=1}
   if b>160&&b-r>20&&b-g>10{blue+=1}
   if min(r,min(g,b))>220{white+=1}
  }}
  if skin>=5&&blue>=10 {heroes.append(["x":x,"y":y,"skinPixels":skin,"bluePixels":blue,"whitePixels":white])}
 }}
 func whiteCount(_ rect:CGRect)->Int {
  var count=0
  for y in Int(rect.minY)..<Int(rect.maxY){for x in Int(rect.minX)..<Int(rect.maxX){let p=(y*w+x)*4;if min(bytes[p],min(bytes[p+1],bytes[p+2]))>220{count+=1}}}
  return count
 }
 let menuCounts=[whiteCount(CGRect(x:250,y:185,width:75,height:25)),whiteCount(CGRect(x:230,y:215,width:115,height:35)),whiteCount(CGRect(x:230,y:325,width:115,height:35))]
 let menuCandidate=menuCounts[0]>10 && menuCounts[1]>40 && menuCounts[2]>40
 return ["scope":"Visible HUD OCR and heuristic image candidates only", "hudRead":withHUD,"sceneText":withSceneText ? readText(img) : [],"numericContextPrefix":"123", "values":values,"directValues":directValues,"directReadings":directReadings,"directCandidates":directCandidates,"contextualKeyCandidates":contextualKeyCandidates,"raw":raw,"heroCandidates":heroes,"orangeMaxRun":orangeMaxRun,"menuTextRegionWhitePixels":menuCounts,"menuCandidate":menuCandidate,"boardBlackFraction":Double(black)/Double(total),"elapsedSeconds":Date().timeIntervalSince(started)]
}
func emit(_ filename:String,withHUD:Bool=true,withSceneText:Bool=false){do{let d=try JSONSerialization.data(withJSONObject:inspect(filename,withHUD:withHUD,withSceneText:withSceneText),options:[.sortedKeys]);print(String(data:d,encoding:.utf8)!)}catch{print("{\"error\":\"encoding failure\"}")};fflush(stdout)}
if CommandLine.arguments.count>1{emit(CommandLine.arguments[1])}else{while let s=readLine(){
 if let data=s.data(using:.utf8),let request=(try? JSONSerialization.jsonObject(with:data)) as? [String:Any],let filename=request["path"] as? String{
  emit(filename,withHUD:request["readHUD"] as? Bool ?? true,withSceneText:request["readSceneText"] as? Bool ?? false)
 }else{emit(s)}
}}
