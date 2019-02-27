tap2go Server
=============

We are entering a new age of micro-mobility, which has grown to solve the last mile problem. Originally stemming from
telecoms, the last mile describes the stretch between the infrastructure arteries and the final destination. The last
mile is everywhere: the gap between the train station and your house, or the gap between the bus routes and the office.
Micro-mobility is a natural solution to this problem. Low cost, low capacity infrastructure will allow people to cover
short distances in minimal time.

There are a number of forms that micro-mobility comes in such as bicycles, scooters,
and skateboards. In the last two years, following the large scale success of ride share companies like Uber and Lyft,
the market for such transport has grown significantly; on-demand micro-mobility solutions are seeing a massive adoption
rate. We believe that usability is the key to ensuring widespread adoption. To contend with more expensive options
such as ride sharing we need to minimize the loss of convenience to make the savings worth it. Traditional micro-
mobility systems such as the bike sharing platform in place in London are clunky and unapproachable (not to mention
plagued with instability and crashes) and we believe there is a better way.

This booklet is the system reference document for the tap2go bike rental platform. It is an open-source, fully
featured, and free to use rental software package for the next age of transport. We have built the system to be as
flexible, organized, and generic as possible such that anyone with any amount of resources may implement their own bike-
sharing scheme. The hardware is also open source, and is built with off-the-shelf parts making this a low cost solution
to the micro-mobility problem.

.. toctree::
   :maxdepth: 2
   :caption: Design

   design/system-design
   design/data-design
   design/testing
   design/bike-protocol
   design/authentication
   design/style-guide

.. toctree::
   :maxdepth: 3
   :caption: Server Reference

   server/models
   server/permissions
   server/views
   server/server
   server/service
   server/serializer
   server/events

.. toctree::
   :maxdepth: 2
   :caption: Fake Bike Reference

   fakebike/fakebike

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
