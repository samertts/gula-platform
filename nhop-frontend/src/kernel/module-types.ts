export interface NHOPModule {

  id: string;
  title: string;

  mount(
    root: HTMLElement,
    ctx: any
  ): void | Promise<void>;

  unmount?(): void;
}
