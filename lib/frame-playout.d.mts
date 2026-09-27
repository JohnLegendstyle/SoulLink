export class FramePlayout {
  rate:number;
  reset():void;
  receive(now:number,target:number):void;
  take(now:number,available:number):number;
}
