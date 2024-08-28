import React from "react";
import { afterAll, afterEach, beforeAll, describe, expect, it } from "vitest";
import AnalyzeMenu from "../src/components/AnalyzeMenu";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { userEvent, render, screen, waitFor } from "./testUtils";
import { setupServer } from "msw/node";
import { analysisStepsHandler, selectiveAnalysisHandler } from "./fakeData";
import { HttpResponse, http } from "msw";
import { getServerUrl } from "../src/api/getServerUrl";

const server = setupServer();

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

/**
 * Tests opening the AnalyzeMenu dropdown and clicking an analysis button
 */
const testSelectAnalysis = async (
  filter: string,
  analyzeFilter: "all" | "selected",
  checkedExperiments: { [exp: string]: boolean } = {}
) => {
  render(
    <MemoryRouter initialEntries={["/"]}>
      <Routes>
        <Route
          path="/"
          element={
            <AnalyzeMenu
              analyzeFilter={analyzeFilter}
              checkedExperiments={checkedExperiments}
            />
          }
        />
        <Route path="/queue" element={<p>Queue Page</p>} />
      </Routes>
    </MemoryRouter>
  );
  const user = userEvent.setup();

  await user.click(
    screen.getByRole("button", {
      name: analyzeFilter === "all" ? "Analyze All" : "Analyze Selected",
    })
  );
  await waitFor(() => {
    expect(screen.getByText(filter)).toBeVisible();
  });
  await user.click(screen.getByText(filter));
  await user.click(screen.getByText("Analyze"));
  await waitFor(() => {
    expect(screen.getByText("Queue Page")).toBeInTheDocument();
  });
};

describe("AnalyzeMenu", () => {
  it("loads", () => {
    server.use(analysisStepsHandler)
    render(
      <MemoryRouter initialEntries={["/"]}>
        <AnalyzeMenu analyzeFilter="all" checkedExperiments={{}} />
      </MemoryRouter>
    );
    expect(true).toBe(true);
  });
  // it("performs conversions + processing when 'All' option is clicked", async () => {
  //   server.use(
  //     selectiveAnalysisHandler({
  //       convert_unconverted: true,
  //       process_converted: true,
  //     })
  //   );
  //   await testSelectAnalysis("All", "all");
  // });
  it("performs conversions only when 'Unconverted Data' option is clicked", async () => {
    server.use(
      selectiveAnalysisHandler({
        steps_to_analyze: [true],
      }),
      analysisStepsHandler
    );
    await testSelectAnalysis("Unconverted Data → Converted Data", "all");
  });
  // it("performs processing only when 'Process Only' option is clicked", async () => {
  //   server.use(
  //     selectiveAnalysisHandler({
  //       convert_unconverted: false,
  //       process_converted: true,
  //     })
  //   );
  //   await testSelectAnalysis("Process Only", "all");
  // });
  it("can request analysis for only some selected experiments", async () => {
    server.use(
      selectiveAnalysisHandler({
        steps_to_analyze: [true],
        pattern: "(ID-NONE|ID-UNC-CON)",
      }),
      analysisStepsHandler
    );
    const checkedExperiments = {
      "ID-NONE": true,
      "ID-UNC-CON": true,
    };
    await testSelectAnalysis("Unconverted Data → Converted Data", "selected", checkedExperiments);
  });
  it("displays error if request unsuccessful", async () => {
    server.use(
      http.post(`${getServerUrl()}/analyses`, () => {
        return HttpResponse.text("Error", { status: 400 });
      }),
      analysisStepsHandler
    );

    render(
      <MemoryRouter>
        <AnalyzeMenu analyzeFilter="all" checkedExperiments={{}} />
      </MemoryRouter>
    );
    const user = userEvent.setup();

    await user.click(screen.getByRole("button", { name: "Analyze All" }));
    await waitFor(() => {
      expect(screen.getByText("Unconverted Data → Converted Data")).toBeVisible();
    });
    await user.click(screen.getByText("Unconverted Data → Converted Data"));
    await user.click(screen.getByText("Analyze"));
    await waitFor(() => {
      expect(
        screen.getByText("Network response was not ok")
      ).toBeInTheDocument();
    });
  });
});
