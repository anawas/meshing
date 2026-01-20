// Minimal type definitions for @kitware/vtk.js modules used in this project

declare module '@kitware/vtk.js/Rendering/Profiles/Geometry';

declare module '@kitware/vtk.js/Rendering/Misc/FullScreenRenderWindow' {
  export interface vtkFullScreenRenderWindow {
    getRenderer(): vtkRenderer;
    getRenderWindow(): vtkRenderWindow;
  }

  export default {
    newInstance(config?: { container: HTMLElement | null }): vtkFullScreenRenderWindow;
  };
}

declare module '@kitware/vtk.js/Rendering/Core/Actor' {
  export interface vtkProperty {
    setRepresentation(mode: number): void;
  }

  export interface vtkActor {
    setMapper(mapper: any): void;
    getProperty(): vtkProperty;
    setVisibility(visible: boolean): void;
  }

  export default {
    newInstance(): vtkActor;
  };
}

declare module '@kitware/vtk.js/Rendering/Core/Mapper' {
  export interface vtkMapper {
    setInputData(data: any): void;
    modified(): void;
  }

  export default {
    newInstance(): vtkMapper;
  };
}

declare module '@kitware/vtk.js/Interaction/Style/InteractorStyleManipulator' {
  export interface vtkInteractorStyleManipulator {}

  export default {
    newInstance(): vtkInteractorStyleManipulator;
  };
}

declare module '@kitware/vtk.js/Interaction/Style/InteractorStyleManipulator/Presets' {
  export interface InteractorStyleDefinition {
    type: string;
    options: Record<string, any>;
  }

  export default {
    applyDefinitions(
      definitions: InteractorStyleDefinition[],
      style: any
    ): void;
  };
}

declare module '@kitware/vtk.js/Rendering/Core/CellPicker' {
  export interface vtkCellPicker {
    setPickFromList(flag: number): void;
    setTolerance(tolerance: number): void;
    initializePickList(): void;
    addPickList(actor: any): void;
    pick(point: number[], renderer: any): void;
    getActors(): any[];
    getCellId(): number;
  }

  export default {
    newInstance(): vtkCellPicker;
  };
}

declare module '@kitware/vtk.js/IO/XML/XMLPolyDataReader' {
  export interface vtkXMLPolyDataReader {
    parseAsArrayBuffer(buffer: ArrayBuffer): void;
    getOutputData(index: number): vtkPolyData;
  }

  export default {
    newInstance(): vtkXMLPolyDataReader;
  };
}

// Common VTK types
interface vtkDataArray {
  getData(): any[];
}

interface vtkCellData {
  getArrayByName(name: string): vtkDataArray | null;
}

interface vtkPolyData {
  getCellData(): vtkCellData;
}

interface vtkRenderer {
  addActor(actor: any): void;
  getActors(): any[];
  resetCamera(): void;
}

interface vtkRenderWindow {
  getInteractor(): vtkInteractor;
  render(): void;
}

interface vtkInteractorCallData {
  position: { x: number; y: number };
  controlKey: boolean;
  shiftKey: boolean;
}

interface vtkInteractor {
  setInteractorStyle(style: any): void;
  onLeftButtonPress(callback: (callData: vtkInteractorCallData) => void): void;
}

// Extend Window interface for global functions
interface Window {
  resetCamera?: () => void;
  toggleWireframe?: () => void;
  downloadFromCloud?: () => Promise<void>;
}
