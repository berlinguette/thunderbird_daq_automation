import { Flex, Tab, TabList, TabPanel, TabPanels, Tabs } from "@chakra-ui/react";
import NavBar from "../components/NavBar";
import Inventory from "../components/Inventory";

function Home() {

  return (
    <Flex flexDirection="column" gap={10} padding={6}>
      <NavBar />
      <Flex>
        <Tabs w="100%">
          <TabList w="fit-content">
            <Tab>All</Tab>
            <Tab>To be converted</Tab>
            <Tab>To be processed</Tab>
          </TabList>

          <TabPanels>
            <TabPanel>
              <Inventory />
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
