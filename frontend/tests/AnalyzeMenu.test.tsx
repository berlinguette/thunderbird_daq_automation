import React from "react";
import { afterAll, afterEach, beforeAll, describe, expect, it } from "vitest";
import AnalyzeMenu from "../src/components/AnalyzeMenu";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { fireEvent, render, screen, waitFor } from "./testUtils";
import { setupServer } from "msw/node";
import { analysisHandler } from "./fakeData";
import { HttpResponse, http } from "msw";
import { getServerUrl } from "../src/api/getServerUrl";

const server = setupServer(analysisHandler);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

/**
 * Tests opening the AnalyzeMenu dropdown and clicking an analysis button
 */
const testSelectAnalysis = async (
  filter: "All" | "Convert Only" | "Process Only",
  analyzeFilter: "all" | "selected",
  checkedExperiments: { [exp: string]: boolean } = {}
) => {

  render(
    <MemoryRouter initialEntries={["/"]}>
      <Routes>
        <Route
          path="/"
          element={<AnalyzeMenu analyzeFilter={analyzeFilter} checkedExperiments={checkedExperiments} />}
        />
        <Route
          path="/queue"
          element={<p>Queue Page</p>}
        />
      </Routes>
    </MemoryRouter>
  );

  fireEvent.click(screen.getByRole("button"));
  await waitFor(() => {
    expect(screen.getByText(filter)).toBeVisible();
  });
  fireEvent.click(screen.getByText(filter));
  await waitFor(() => {
    expect(screen.getByText("Queue Page")).toBeInTheDocument();
  });
}

describe("AnalyzeMenu", () => {
  it("loads", () => {
    render(
      <MemoryRouter initialEntries={["/"]}>
        <AnalyzeMenu analyzeFilter="all" checkedExperiments={{}} />
      </MemoryRouter>
    );
    expect(true).toBe(true);
  });
  it("performs conversions + processing when 'All' option is clicked", async () => {
    await testSelectAnalysis("All", "all");
  });
  it("performs conversions only when 'Convert Only' option is clicked", async () => {
    await testSelectAnalysis("Convert Only", "all");
  });
  it("performs processing only when 'Process Only' option is clicked", async () => {
    await testSelectAnalysis("Process Only", "all");
  });
  it("can request analysis for only some selected experiments", async () => {
    const checkedExperiments = {
      "ID-NONE": true,
      "ID-UNC-CON": true
    }
    await testSelectAnalysis("All", "selected", checkedExperiments);
  });
  it("displays error if request unsuccessful", async () => {
    server.use(http.post(`${getServerUrl()}/analyses`, () => {
      return HttpResponse.text("Error", { status: 400 });
    }));

    render(
      <MemoryRouter>
        <AnalyzeMenu analyzeFilter="all" checkedExperiments={{}} />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByRole("button"));
    await waitFor(() => {
      expect(screen.getByText("All")).toBeVisible();
    });
    fireEvent.click(screen.getByText("All"));
    await waitFor(() => {
      expect(screen.getByText("Network response was not ok")).toBeInTheDocument();
    });
  })
});