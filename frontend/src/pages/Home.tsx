import { Box, Flex, Spacer, Tab, TabList, TabPanel, TabPanels, Tabs } from "@chakra-ui/react";
import NavBar from "../components/NavBar";

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
              <p>One</p>
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
