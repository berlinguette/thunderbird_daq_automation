import { Flex, Tab, TabList, TabPanel, TabPanels, Tabs } from "@chakra-ui/react";
import NavBar from "../components/NavBar";
import InventoryTable from "../components/InventoryTable";

function Home() {

  return (
    <Flex flexDirection="column" gap={10} padding={6}>
      <NavBar />
      <Flex>
        <Tabs>
          <TabList>
            <Tab>All</Tab>
            <Tab>To be converted</Tab>
            <Tab>To be processed</Tab>
          </TabList>

          <TabPanels>
            <TabPanel>
              <InventoryTable />
            </TabPanel>
            <TabPanel>
              <p>Two</p>
            </TabPanel>
            <TabPanel>
              <p>Three</p>
            </TabPanel>
          </TabPanels>
        </Tabs>
      </Flex>
    </Flex>
  )
}

export default Home
