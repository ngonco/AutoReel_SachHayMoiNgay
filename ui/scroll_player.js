'use strict';
// Draw server-rasterized tiles. Layout and all motion parameters come from text_track.
class ScrollTextLayer {
  constructor(plan,loadImage,onReady) {
    this.plan=plan;this.track=plan.text_track;this.loadImage=loadImage;this.onReady=onReady;
    this.images=new Map();this.pending=new Map();this.error=null;
    this.canvas=document.createElement('canvas');
    this.canvas.width=this.track.rect.width;this.canvas.height=this.track.rect.height;
    this.ctx=this.canvas.getContext('2d');
  }
  static async create(plan,loadImage,onReady) {
    const layer=new ScrollTextLayer(plan,loadImage,onReady);
    layer.mask=await loadImage(`/api/scroll_asset/${plan.plan_id}/mask`);
    await layer.prepare(0);
    return layer;
  }
  offset(time) {
    const s=this.track;
    if(!s.distance)return s.initial_offset;
    const progress=Math.max(0,Math.min(1,(time-s.scroll_start)/(s.scroll_end-s.scroll_start)));
    return s.initial_offset+Math.floor(s.distance*progress+.5);
  }
  visible(time) {
    const offset=this.offset(time),height=this.track.rect.height;
    return this.track.tiles.filter(tile=>tile.y-offset<height&&tile.y+tile.height-offset>0);
  }
  fetchTile(index) {
    if(this.images.has(index))return Promise.resolve(this.images.get(index));
    if(!this.pending.has(index)) {
      const promise=this.loadImage(`/api/scroll_asset/${this.plan.plan_id}/${index}`).then(image=>{
        this.images.set(index,image);this.pending.delete(index);
        while(this.images.size>12)this.images.delete(this.images.keys().next().value);
        this.onReady?.();return image;
      }).catch(error=>{this.pending.delete(index);this.error=error;throw error;});
      this.pending.set(index,promise);
    }
    return this.pending.get(index);
  }
  prepare(time) {return Promise.all(this.visible(time).map(tile=>this.fetchTile(tile.index)));}
  draw(ctx,time,width,height) {
    if(this.error)throw this.error;
    const tiles=this.visible(time),ready=tiles.every(tile=>this.images.has(tile.index));
    if(!ready){this.prepare(time).catch(()=>{});return false;}
    // Look ahead without moving the shared playback clock.
    this.prepare(Math.min(this.track.duration,time+3)).catch(()=>{});
    const pen=this.ctx,rect=this.track.rect,offset=this.offset(time);
    pen.clearRect(0,0,rect.width,rect.height);
    pen.globalCompositeOperation='source-over';
    for(const tile of tiles)pen.drawImage(this.images.get(tile.index),0,tile.y-offset);
    pen.globalCompositeOperation='destination-in';pen.drawImage(this.mask,0,0);
    pen.globalCompositeOperation='source-over';
    const fade=this.track.fade_seconds;
    ctx.save();ctx.globalAlpha=Math.max(0,Math.min(1,time/fade,(this.track.duration-time)/fade));
    ctx.drawImage(this.canvas,rect.x*width/1080,rect.y*height/1920,rect.width*width/1080,rect.height*height/1920);
    ctx.restore();return true;
  }
}
if(typeof module!=='undefined')module.exports={ScrollTextLayer};
