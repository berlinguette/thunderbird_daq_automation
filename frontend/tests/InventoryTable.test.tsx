import React, { useState } from "react";
import { userEvent, render, screen } from "./testUtils";
import { describe, expect, it } from "vitest";
import InventoryTable from "../src/components/inventory/InventoryTable";
import { Experiment } from "../src/types/Experiment";

const fakeData: Experiment[] = [
  {
    id: "ID-100",
    props: {
      unconverted_mtime: 100,
      converted_mtime: 200,
      processed_mtime: 500,
      overridden: false
    }
  },
  {
    id: "ID-101",
    props: {
      unconverted_mtime: 200,
      converted_mtime: 100,
      processed_mtime: 400,
      overridden: false
    }
  },
  {
    id: "ID-102",
    props: {
      unconverted_mtime: 50,
      converted_mtime: 300,
      processed_mtime: 300,
      overridden: false
    }
  }
];

const TestEnv = ({ experimentsList }: { experimentsList: Experiment[] }) => {
  const [checkedExperiments, setCheckedExperiments] = useState({});
  return (
    <InventoryTable
      experimentsList={experimentsList}
      checkedExperiments={checkedExperiments}
      setCheckedExperiments={setCheckedExperiments}
    />
  );
};

const testSort = async (
  experimentIdsOrder: string[],
  clickText: string | null = null,
  clickTwice: boolean = false
) => {
  const user = userEvent.setup();
  render(<TestEnv experimentsList={fakeData} />);
  if (clickText) {
    const header = screen.getByText(clickText);
    await user.click(header);
    if (clickTwice) await user.click(header);
  }

  for (let i = 0; i < experimentIdsOrder.length - 1; i++) {
    const firstExp = screen.getByText(experimentIdsOrder[i]);
    const secondExp = screen.getByText(experimentIdsOrder[i + 1]);
    expect(firstExp.compareDocumentPosition(secondExp)).toBe(2);
  }
};

describe("Inventory table", () => {
  it("is initially sorted by ID", async () => {
    await testSort(["ID-100", "ID-101", "ID-102"]);
  });
  it("reverse sorts by ID when clicking corresponding header", async () => {
    await testSort(["ID-102", "ID-101", "ID-100"], "ID");
  });
  it("sorts by Unconverted Data when clicking corresponding header", async () => {
    await testSort(["ID-102", "ID-100", "ID-101"], "Unconverted Data");
  });
  it("reverse sorts by Unconverted Data when clicking corresponding header twice", async () => {
    await testSort(["ID-101", "ID-100", "ID-102"], "Unconverted Data", true);
  });
  it("sorts by Converted Data when clicking corresponding header", async () => {
    await testSort(["ID-101", "ID-100", "ID-102"], "Converted Data");
  });
  it("reverse sorts by Converted Data when clicking corresponding header twice", async () => {
    await testSort(["ID-102", "ID-100", "ID-101"], "Converted Data", true);
  });
  it("sorts by Processed Data when clicking corresponding header", async () => {
    await testSort(["ID-102", "ID-101", "ID-100"], "Processed Data");
  });
  it("reverse sorts by Processed Data when clicking corresponding header twice", async () => {
    await testSort(["ID-100", "ID-101", "ID-102"], "Processed Data", true);
  });
});