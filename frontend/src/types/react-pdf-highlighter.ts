export interface SelectionPosition {
  boundingRect: {
    x1: number;
    y1: number;
    x2: number;
    y2: number;
    width: number;
    height: number;
    pageNumber: number;
  };
  rects: Array<{
    x1: number;
    y1: number;
    x2: number;
    y2: number;
    width: number;
    height: number;
    pageNumber: number;
  }>;
  pageNumber: number;
}

export interface SelectionContent {
  text: string;
  image?: string;
}

export interface HighlightComment {
  text: string;
  emoji?: string;
}

export type ViewportToScaledFunction = (rect: {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  pageNumber: number;
}) => {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  width: number;
  height: number;
  pageNumber: number;
};

export type ScreenshotFunction = (position: SelectionPosition) => string;